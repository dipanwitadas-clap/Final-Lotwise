# Copyright (c) 2026, BusinessThat.Works and contributors
# For license information, please see license.txt
"""Generic helpers to run a long document method as a background job and report
progress to the form (same pattern as Tea Lot Image Import's scan).

The target doctype must have these fields: job_status (Select: Queued /
Processing / Done / Error), job_action (Data), job_processed (Int),
job_total (Int), job_message (Small Text), job_updated (Datetime).
"""

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime

EVENT = "lotwise_job_progress"
STALE_JOB_THRESHOLD_MINUTES = 30
ACTIVE = ("Queued", "Processing")


def start_job(doctype, name, action, job_method, queue="long", timeout=3000):
	"""Mark the document Queued and enqueue `job_method(name=, action=)`."""
	status = frappe.db.get_value(doctype, name, "job_status")
	if status in ACTIVE:
		frappe.throw(_("A background job is already running for this document."))

	frappe.db.set_value(
		doctype,
		name,
		{
			"job_status": "Queued",
			"job_action": action,
			"job_processed": 0,
			"job_total": 0,
			"job_message": "",
			"job_updated": now_datetime(),
		},
		update_modified=False,
	)
	frappe.enqueue(
		job_method,
		queue=queue,
		timeout=timeout,
		job_id=f"{doctype}_{name}_job",
		deduplicate=False,
		enqueue_after_commit=True,
		name=name,
		action=action,
	)
	return {"queued": True, "action": action}


def mark_processing(doctype, name):
	frappe.db.set_value(
		doctype,
		name,
		{"job_status": "Processing", "job_updated": now_datetime()},
		update_modified=False,
	)
	frappe.db.commit()


def notify(doctype, name, processed, total, current="", commit=True):
	"""Persist counters (without touching `modified`, so the running document's
	own save() doesn't hit a timestamp mismatch) and publish a realtime tick."""
	frappe.db.set_value(
		doctype,
		name,
		{"job_processed": processed, "job_total": total, "job_updated": now_datetime()},
		update_modified=False,
	)
	if commit:
		frappe.db.commit()
	frappe.publish_realtime(
		EVENT,
		{
			"docname": name,
			"processed": processed,
			"total": total,
			"current": current,
			"phase": "running",
		},
		doctype=doctype,
		docname=name,
	)


def finish_job(doctype, name, status="Done", message=""):
	"""Always call from `finally`: forces the document out of Queued/Processing
	and publishes the terminal event so the form never stays locked."""
	try:
		current = frappe.db.get_value(doctype, name, "job_status")
		if current in ACTIVE or status == "Error":
			frappe.db.set_value(
				doctype,
				name,
				{"job_status": status, "job_message": message or "", "job_updated": now_datetime()},
				update_modified=False,
			)
		else:
			frappe.db.set_value(doctype, name, "job_message", message or "", update_modified=False)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"{doctype}: finish_job failed")

	processed, total, final = frappe.db.get_value(
		doctype, name, ["job_processed", "job_total", "job_status"]
	) or (0, 0, "Error")
	frappe.publish_realtime(
		EVENT,
		{
			"docname": name,
			"processed": processed or 0,
			"total": total or 0,
			"phase": "done",
			"status": final,
			"message": message or "",
		},
		doctype=doctype,
		docname=name,
	)


def unlock_stale_jobs(doctype, describe=None):
	"""Backstop for killed workers (SIGKILL / OOM / restart): `finish_job` cannot
	run then, so documents would stay locked forever. `describe(name)` may return
	a more specific message (e.g. how many rows were already done)."""
	cutoff = add_to_date(now_datetime(), minutes=-STALE_JOB_THRESHOLD_MINUTES)
	stale = frappe.get_all(
		doctype,
		filters={"job_status": ["in", list(ACTIVE)], "job_updated": ["<", cutoff]},
		pluck="name",
	)
	for name in stale:
		message = None
		if describe:
			try:
				message = describe(name)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"{doctype}: stale-job describe failed")
		finish_job(
			doctype,
			name,
			"Error",
			message or _("Background job timed out or the worker crashed. Please retry."),
		)
