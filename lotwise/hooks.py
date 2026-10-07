app_name = "lotwise"
app_title = "Lotwise"
app_publisher = "BusinessThat.Works"
app_description = " Tea lot capture and evaluation system "
app_email = "dipanwita.das@businessthat.works"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lotwise",
# 		"logo": "/assets/lotwise/logo.png",
# 		"title": "Lotwise",
# 		"route": "/lotwise",
# 		"has_permission": "lotwise.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lotwise/css/lotwise.css"
# app_include_js = "/assets/lotwise/js/lotwise.js"

# include js, css files in header of web template
# web_include_css = "/assets/lotwise/css/lotwise.css"
# web_include_js = "/assets/lotwise/js/lotwise.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lotwise/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lotwise/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lotwise.utils.jinja_methods",
# 	"filters": "lotwise.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lotwise.install.before_install"
# after_install = "lotwise.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lotwise.uninstall.before_uninstall"
# after_uninstall = "lotwise.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lotwise.utils.before_app_install"
# after_app_install = "lotwise.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lotwise.utils.before_app_uninstall"
# after_app_uninstall = "lotwise.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lotwise.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lotwise.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": ["lotwise.lotwise.doctype.tea_lot_image_import.tea_lot_image_import.unlock_stale_scans"],
}

# Testing
# -------

# before_tests = "lotwise.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lotwise.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lotwise.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lotwise.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lotwise.utils.before_request"]
# after_request = ["lotwise.utils.after_request"]

# Job Events
# ----------
# before_job = ["lotwise.utils.before_job"]
# after_job = ["lotwise.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lotwise.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
# fixtures = [{"doctype": "Role", "filters": [["role_name", "in", ["Tea Manager", "Taster", "Data Entry"]]]}]
fixtures = [
	{
		"doctype": "Role",
		"filters": [["role_name", "in", ["Tea Manager", "Taster", "Data Entry"]]],
	},
	{
		"doctype": "Custom Field",
		"filters": [
			["dt", "=", "Purchase Order Item"],
			["module", "=", "Lotwise"],
		],
	},
]

ignore_links_on_delete = [
	"Tea Lot Import",
]
