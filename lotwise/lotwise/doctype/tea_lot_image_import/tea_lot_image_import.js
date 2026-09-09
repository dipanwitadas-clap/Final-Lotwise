// Copyright (c) 2026, BusinessThat.Works and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tea Lot Image Import", {
	onload(frm) {
		_register_realtime(frm);
	},

	refresh(frm) {
		frm.clear_custom_buttons();
		_render_progress_bar(frm);
		_setup_buttons(frm);
		_apply_child_table_styles(frm);
		_apply_processing_lock(frm);
	},
});

// ─────────────────────────────────────────────────────────────────────────────
// PROCESSING LOCK — freeze fields/save while a scan runs (progress bar stays live)
// ─────────────────────────────────────────────────────────────────────────────

function _apply_processing_lock(frm) {
	const should_lock = frm.doc.scan_status === "Processing";

	// Idempotent — only act on the transition, so the realtime handler (fires
	// once per page) doesn't re-set the headline on every tick.
	if (should_lock === !!frm._tea_lot_locked) return;
	frm._tea_lot_locked = should_lock;

	if (should_lock) {
		// Lock editing + saving, but DO NOT use a freeze overlay — the progress
		// bar (HTML field + realtime DOM updates) must stay visible.
		frm.disable_save();
		frm.set_read_only();
		frm.dashboard.set_headline(
			__("🔒 Scanning images — the form is locked until it completes.")
		);
	} else {
		// Release the lock SYMMETRICALLY. disable_save()/set_read_only() are
		// sticky: refresh() never resets them on its own. Without reversing
		// them here the form stays read-only + un-savable until a hard refresh.
		frm.enable_save(); // reverse frm.disable_save()
		frm.fetch_permissions(); // reverse frm.set_read_only() — restore write perms
		frm.refresh_fields(); // fields were rendered read-only; re-render now editable
		frm.dashboard.clear_headline();
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// PROGRESS BAR
// ─────────────────────────────────────────────────────────────────────────────

const PROGRESS_BAR_ID = "tea-lot-progress-bar";

function _progress_counts(frm) {
	const rows = frm.doc.source_images || [];
	const total = frm.doc.total_pages || 0;
	const processed = frm.doc.processed_pages || 0;
	const ok = rows.filter((r) => r.status === "Extracted").length;
	const failed = rows.filter((r) => r.status === "Failed").length;
	const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
	return { total, processed, ok, failed, pct };
}

// Green only when nothing failed; amber on partial failure; red when all failed.
function _progress_color(status, ok, failed) {
	if (status === "Processing") return "#0d6efd";
	if (failed > 0 && ok === 0) return "#dc3545";
	if (failed > 0) return "#fd7e14";
	return "#198754";
}

// "2 / 2 pages read" plus a "✓ 1 read · ✗ 1 failed" line when any failed.
function _progress_count_html(processed, total, ok, failed) {
	let html = `${processed} / ${total} pages read`;
	if (failed > 0) {
		html +=
			`<br><span style="color:#198754;">✓ ${ok} read</span>` +
			` &nbsp;·&nbsp; <span style="color:#dc3545; font-weight:600;">✗ ${failed} failed</span>`;
	}
	return html;
}

function _render_progress_bar(frm) {
	const status = frm.doc.scan_status;

	if (!status || status === "Not Scanned") {
		frm.set_df_property("progress_bar_html", "options", "");
		frm.refresh_field("progress_bar_html");
		return;
	}

	const { total, processed, ok, failed, pct } = _progress_counts(frm);
	const color = _progress_color(status, ok, failed);

	const html = `
		<style>
			@keyframes tea-lot-pulse {
				0%,100% { opacity:1; transform:scale(1); }
				50%      { opacity:.35; transform:scale(1.6); }
			}
		</style>
		<div id="${PROGRESS_BAR_ID}" style="margin:4px 0 12px;">
			<div style="display:flex; justify-content:space-between; align-items:center;
			            margin-bottom:5px; font-size:13px;">
				<span style="font-weight:600; color:var(--text-color); display:flex; align-items:center; gap:6px;">
					<span id="${PROGRESS_BAR_ID}-pulse" style="
						display:${status === "Processing" ? "inline-block" : "none"};
						width:8px; height:8px; background:${color}; border-radius:50%;
						animation:tea-lot-pulse 1.2s ease-in-out infinite;">
					</span>
					${__("Scan Progress")}
				</span>
				<span id="${PROGRESS_BAR_ID}-pct" style="font-weight:700; color:${color};">${pct}%</span>
			</div>
			<div style="background:var(--input-disabled-bg); border-radius:6px; height:10px; overflow:hidden;">
				<div id="${PROGRESS_BAR_ID}-fill"
				     style="width:${pct}%; height:100%; background:${color};
				            border-radius:6px; transition:width 0.5s ease;">
				</div>
			</div>
			<div id="${PROGRESS_BAR_ID}-count"
			     style="text-align:center; margin-top:4px; font-size:12px; color:var(--text-muted);">
				${_progress_count_html(processed, total, ok, failed)}
			</div>
			<div id="${PROGRESS_BAR_ID}-file"
			     style="font-size:11px; color:var(--text-muted); margin-top:3px;
			            overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:none;">
			</div>
		</div>`;

	frm.set_df_property("progress_bar_html", "options", html);
	frm.refresh_field("progress_bar_html");
}

function _update_progress_bar_dom(frm, current_file) {
	const bar = document.getElementById(PROGRESS_BAR_ID);
	if (!bar) {
		_render_progress_bar(frm);
		return;
	}

	const { total, processed, ok, failed, pct } = _progress_counts(frm);
	const color = _progress_color(frm.doc.scan_status, ok, failed);

	const fill = document.getElementById(`${PROGRESS_BAR_ID}-fill`);
	const pct_el = document.getElementById(`${PROGRESS_BAR_ID}-pct`);
	const count = document.getElementById(`${PROGRESS_BAR_ID}-count`);
	const file_el = document.getElementById(`${PROGRESS_BAR_ID}-file`);

	if (fill) {
		fill.style.width = `${pct}%`;
		fill.style.background = color;
	}
	if (pct_el) {
		pct_el.textContent = `${pct}%`;
		pct_el.style.color = color;
	}
	if (count) count.innerHTML = _progress_count_html(processed, total, ok, failed);

	if (file_el) {
		if (current_file) {
			file_el.style.display = "block";
			file_el.innerHTML = `${__("Reading")}: <strong>${frappe.utils.escape_html(
				current_file
			)}</strong>`;
		} else {
			file_el.style.display = "none";
		}
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// WEBSOCKET
// ─────────────────────────────────────────────────────────────────────────────

function _register_realtime(frm) {
	frappe.realtime.off("tea_scan_progress");

	frappe.realtime.on("tea_scan_progress", function (data) {
		if (data.docname !== frm.doc.name) return;

		frm.doc.scan_status = "Processing";
		frm.doc.processed_pages = data.processed;
		frm.doc.total_pages = data.total;

		_apply_processing_lock(frm);
		_update_progress_bar_dom(frm, data.current_file);

		if (data.phase === "done") {
			const message = data.scan_error
				? __("Scan {0} — {1}", [data.status || "finished", data.scan_error])
				: __("Scan {0} — {1}/{2} pages", [
						data.status || "finished",
						data.processed,
						data.total,
				  ]);
			frappe.show_alert({
				message,
				indicator:
					data.status === "Error"
						? "red"
						: data.status === "Partial"
						? "orange"
						: "green",
			});
			setTimeout(() => frm.reload_doc(), 1500);
		}
	});
}

// ─────────────────────────────────────────────────────────────────────────────
// BUTTONS
// ─────────────────────────────────────────────────────────────────────────────

function _setup_buttons(frm) {
	const is_processing = frm.doc.scan_status === "Processing";
	if (is_processing) return; // locked — no actions while a scan is running

	frm.add_custom_button(__("Upload Source Images"), () => {
		new frappe.ui.FileUploader({
			allow_multiple: true,
			is_private: true,
			restrictions: {
				allowed_file_types: ["image/*"],
				max_file_size: 15 * 1024 * 1024,
			},
			on_success(file) {
				const already = (frm.doc.source_images || []).some(
					(row) => row.file_name === file.file_name
				);
				if (already) {
					frappe.show_alert({
						message: __("{0} is already added.", [file.file_name]),
						indicator: "orange",
					});
					return;
				}
				frm.add_child("source_images", {
					file_name: file.file_name,
					file_url: file.file_url,
				});
				frm.refresh_field("source_images");
				frm.dirty();
			},
		});
	});

	if (frm.is_new()) return;

	frm.add_custom_button(__("Scan Image"), () => {
		if (frm.is_dirty()) {
			frappe.msgprint(__("Please save the document before scanning."));
			return;
		}
		if (!(frm.doc.source_images && frm.doc.source_images.length)) {
			frappe.msgprint(__("Upload at least one source image first."));
			return;
		}
		frappe.confirm(
			__("Extract lot data from the attached images? This will replace the current items."),
			() => _start_scan(frm)
		);
	}).addClass("btn-primary");

	if (["Auction", "Outsourced"].includes(frm.doc.acquisition_channel)) {
		frm.add_custom_button(__("Create Tea Lots"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please save the document before creating Tea Lots."));
				return;
			}
			if (!(frm.doc.items && frm.doc.items.length)) {
				frappe.msgprint(__("No lot rows to create Tea Lots from."));
				return;
			}
			frappe.confirm(__("Create a Tea Lot for each pending row in the table below?"), () =>
				_create_tea_lots(frm)
			);
		});
	}
}

function _create_tea_lots(frm) {
	frm.call({
		doc: frm.doc,
		method: "create_tea_lots",
		freeze: true,
		freeze_message: __("Creating Tea Lots…"),
	}).then((r) => {
		frm.reload_doc();
		const m = r.message || {};
		frappe.show_alert({
			message: __("{0} created, {1} duplicate, {2} error(s)", [
				m.created || 0,
				m.duplicates || 0,
				m.errors || 0,
			]),
			indicator: m.errors ? "orange" : "green",
		});
	});
}

function _start_scan(frm) {
	frappe
		.call({
			method: "lotwise.lotwise.doctype.tea_lot_image_import.tea_lot_image_import.scan_image",
			args: { doc_name: frm.doc.name },
			freeze: true,
			freeze_message: __("Queuing pages for scanning…"),
		})
		.then((r) => {
			if (!r.message || !r.message.success) return;
			frm.doc.scan_status = "Processing";
			frm.doc.total_pages = r.message.total;
			frm.doc.processed_pages = 0;
			_render_progress_bar(frm);
			frm.clear_custom_buttons();
			_setup_buttons(frm);
			_apply_processing_lock(frm);
			frappe.show_alert({ message: r.message.message, indicator: "blue" });
		});
}

// ─────────────────────────────────────────────────────────────────────────────
// CHILD TABLE — "View Error" button on failed rows
// ─────────────────────────────────────────────────────────────────────────────

function _apply_child_table_styles(frm) {
	(frm.doc.source_images || []).forEach((row, idx) => _style_source_row(frm, row, idx));
}

function _style_source_row(frm, row, idx) {
	const grid_row = frm.fields_dict.source_images.grid.grid_rows[idx];
	if (!grid_row) return;

	if (row.error_msg && row.status === "Failed") {
		const cell = $(grid_row.row).find('[data-fieldname="error_msg"]');
		if (!cell.find(".tea-lot-err-btn").length) {
			cell.find(".static-area, .like-disabled-input").hide();
			cell.append(
				$(`<button class="btn btn-xs btn-danger tea-lot-err-btn" style="font-size:11px;">
				       ${__("View Error")}
				   </button>`).on("click", () =>
					frappe.msgprint({
						title: __("Error — {0}", [frappe.utils.escape_html(row.file_name)]),
						message: `<pre style="font-size:11px; white-space:pre-wrap; word-break:break-word;
						                       max-height:400px; overflow:auto;">${frappe.utils.escape_html(
													row.error_msg
												)}</pre>`,
						indicator: "red",
						wide: true,
					})
				)
			);
		}
	}
}
