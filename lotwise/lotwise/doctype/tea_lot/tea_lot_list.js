frappe.listview_settings["Tea Lot"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("Download Eval Import"), function () {
			frappe.call({
				method: "lotwise.lotwise.doctype.tea_lot.tea_lot.download_evaluation_import_xlsx",
				callback: function (r) {
					if (!r.message || !r.message.content) {
						frappe.msgprint(__("No data available for download."));
						return;
					}
					// Decode base64 content
					var binaryStr = atob(r.message.content);
					var byteArray = new Uint8Array(binaryStr.length);
					for (var i = 0; i < binaryStr.length; i++) {
						byteArray[i] = binaryStr.charCodeAt(i);
					}
					var filename = r.message.filename || "tea_evaluation_import.xlsx";
					var blob = new Blob([byteArray], {
						type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					});
					if (navigator.msSaveBlob) {
						navigator.msSaveBlob(blob, filename);
					} else {
						var url = URL.createObjectURL(blob);
						var a = document.createElement("a");
						a.href = url;
						a.download = filename;
						document.body.appendChild(a);
						a.click();
						setTimeout(function () {
							document.body.removeChild(a);
							URL.revokeObjectURL(url);
						}, 100);
					}
				},
			});
		});
	},
};
