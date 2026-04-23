from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from core.database import DB_PATH, get_conn
from core.import_engine import apply_mapping_edits, build_staging, commit_run, detect_profile, parse_files


class PoultryImportWizard(tk.Toplevel):
    def __init__(self, master: tk.Misc | None = None):
        super().__init__(master)
        self.title("استيراد poultry_v4 الذكي")
        self.geometry("1240x780")
        self.minsize(1100, 700)
        self.transient(master)
        self.grab_set()

        self.selected_files: list[str] = []
        self.run_id: int | None = None
        self.batch_mode_var = tk.StringVar(value="create")
        self.merge_mode_var = tk.StringVar(value="replace")
        self.target_batch_var = tk.StringVar(value="")
        self.folder_var = tk.StringVar(value="")
        self.profile_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="جاهز")

        self.cost_types: list[dict[str, Any]] = []
        self.revenue_types: list[dict[str, Any]] = []
        self._load_types()
        self._build_ui()

    def _load_types(self) -> None:
        with get_conn(DB_PATH) as conn:
            self.cost_types = [dict(r) for r in conn.execute("SELECT code, name_ar FROM cost_types WHERE is_active=1 ORDER BY sort_order, id")]
            self.revenue_types = [dict(r) for r in conn.execute("SELECT code, name_ar FROM revenue_types WHERE is_active=1 ORDER BY sort_order, id")]
            profile = conn.execute(
                """
                SELECT id
                FROM import_profiles
                WHERE source_key='poultry_v4' AND is_active=1
                ORDER BY is_default DESC, id ASC
                LIMIT 1
                """
            ).fetchone()
            self.profile_var.set(str(profile["id"]) if profile else "")

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="1) اختيار المصدر").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Button(top, text="اختيار ملف/ملفات", command=self._pick_files).grid(row=1, column=0, sticky="w")
        self.files_label = ttk.Label(top, text="لا يوجد ملفات مختارة", width=88)
        self.files_label.grid(row=1, column=1, sticky="w", padx=8)

        ttk.Button(top, text="اختيار مجلد", command=self._pick_folder).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(top, textvariable=self.folder_var, width=90).grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(top, text="وضع الدفعة").grid(row=3, column=0, sticky="w", pady=(8, 2))
        ttk.Combobox(top, textvariable=self.batch_mode_var, values=["create", "update"], state="readonly", width=18).grid(
            row=3, column=1, sticky="w", padx=8, pady=(8, 2)
        )
        ttk.Label(top, text="Target Batch ID (اختياري)").grid(row=4, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.target_batch_var, width=20).grid(row=4, column=1, sticky="w", padx=8)

        ttk.Button(top, text="2) تحليل وبناء المراجعة", command=self._start_analysis).grid(row=5, column=0, sticky="w", pady=8)
        ttk.Label(top, textvariable=self.status_var, foreground="#184a7d").grid(row=5, column=1, sticky="w", padx=8)

        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(fill="x", padx=10, pady=5)

        middle = ttk.Frame(self, padding=10)
        middle.pack(fill="both", expand=True)
        ttk.Label(middle, text="3) مراجعة وتصنيف البنود").pack(anchor="w")

        self.tree = ttk.Treeview(
            middle,
            columns=("id", "file", "sheet", "row", "label", "qty", "amount", "status", "kind", "code"),
            show="headings",
            height=15,
        )
        headings = {
            "id": "ID",
            "file": "الملف",
            "sheet": "الشيت",
            "row": "الصف",
            "label": "البند",
            "qty": "الكمية",
            "amount": "القيمة",
            "status": "الحالة",
            "kind": "النوع",
            "code": "الكود",
        }
        widths = {
            "id": 70,
            "file": 180,
            "sheet": 110,
            "row": 70,
            "label": 260,
            "qty": 95,
            "amount": 100,
            "status": 100,
            "kind": 85,
            "code": 190,
        }
        for col in self.tree["columns"]:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        map_box = ttk.LabelFrame(self, text="تحرير السطر المحدد", padding=10)
        map_box.pack(fill="x", padx=10, pady=(0, 8))
        self.kind_var = tk.StringVar(value="ignore")
        self.code_var = tk.StringVar(value="")
        self.new_name_var = tk.StringVar(value="")
        self.category_var = tk.StringVar(value="")
        self.unit_var = tk.StringVar(value="")
        self.has_qty_var = tk.IntVar(value=0)

        ttk.Label(map_box, text="النوع").grid(row=0, column=0, sticky="w")
        ttk.Combobox(map_box, textvariable=self.kind_var, values=["ignore", "cost", "revenue"], state="readonly", width=14).grid(
            row=0, column=1, sticky="w", padx=6
        )
        ttk.Label(map_box, text="كود موجود").grid(row=0, column=2, sticky="w")
        self.code_combo = ttk.Combobox(map_box, textvariable=self.code_var, width=42)
        self.code_combo["values"] = [x["code"] for x in self.cost_types] + [x["code"] for x in self.revenue_types]
        self.code_combo.grid(row=0, column=3, sticky="w", padx=6)

        ttk.Label(map_box, text="اسم بند جديد").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(map_box, textvariable=self.new_name_var, width=30).grid(row=1, column=1, sticky="w", padx=6, pady=(8, 0))
        ttk.Label(map_box, text="الفئة").grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(map_box, textvariable=self.category_var, width=20).grid(row=1, column=3, sticky="w", padx=6, pady=(8, 0))
        ttk.Label(map_box, text="الوحدة").grid(row=1, column=4, sticky="w", pady=(8, 0))
        ttk.Entry(map_box, textvariable=self.unit_var, width=20).grid(row=1, column=5, sticky="w", padx=6, pady=(8, 0))
        ttk.Checkbutton(map_box, text="له كمية", variable=self.has_qty_var).grid(row=1, column=6, sticky="w", padx=8, pady=(8, 0))
        ttk.Button(map_box, text="اعتماد التصنيف للسطر", command=self._apply_selected_mapping).grid(row=0, column=6, sticky="e", padx=6)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        ttk.Label(bottom, text="وضع الدمج").pack(side="right")
        ttk.Combobox(bottom, textvariable=self.merge_mode_var, values=["replace", "merge"], state="readonly", width=16).pack(side="right", padx=6)
        ttk.Button(bottom, text="4) تنفيذ الاستيراد", command=self._commit_run).pack(side="right", padx=8)
        ttk.Button(bottom, text="إغلاق", command=self.destroy).pack(side="left")

    def _pick_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="اختر ملفات Excel",
            filetypes=[("Excel files", "*.xlsm *.xlsx *.xls")],
        )
        if not chosen:
            return
        self.selected_files = [str(Path(x)) for x in chosen]
        self.files_label.config(text=f"{len(self.selected_files)} ملف مختار")

    def _pick_folder(self) -> None:
        chosen = filedialog.askdirectory(parent=self, title="اختر مجلد ملفات")
        if chosen:
            self.folder_var.set(chosen)

    def _collect_sources(self) -> list[str]:
        files = list(self.selected_files)
        folder = self.folder_var.get().strip()
        if folder:
            folder_path = Path(folder)
            if folder_path.exists() and folder_path.is_dir():
                for ext in ("*.xlsm", "*.xlsx"):
                    for p in sorted(folder_path.glob(ext)):
                        if not p.name.startswith("~$"):
                            files.append(str(p))
        return list(dict.fromkeys(files))

    def _start_analysis(self) -> None:
        files = self._collect_sources()
        if not files:
            messagebox.showwarning("تنبيه", "اختر ملفات أو مجلد قبل التحليل.", parent=self)
            return
        self.status_var.set("جاري التحقق من القالب...")
        self.update_idletasks()
        profile_match = detect_profile(files)
        if not profile_match.get("matched"):
            msg = "بعض الملفات لا تطابق قالب poultry_v4.\n"
            bad = [x for x in profile_match.get("files", []) if not x.get("ok")]
            if bad:
                msg += "\n".join(f"{x.get('file_name')}: {', '.join(x.get('missing_sheets') or [])}" for x in bad)
            messagebox.showerror("فشل التحقق", msg, parent=self)
            self.status_var.set("فشل التحقق")
            return

        payload = parse_files(files, int(self.profile_var.get() or 0) or None)
        run_id = build_staging(payload, int(self.profile_var.get() or 0) or None, source_ui="desktop", created_by="desktop")
        self.run_id = run_id
        batch_mode = self.batch_mode_var.get().strip() or "create"
        target_batch_id = int(self.target_batch_var.get().strip() or "0")
        with get_conn(DB_PATH) as conn:
            conn.execute(
                """
                UPDATE import_runs
                SET batch_mode=?, target_batch_id=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (batch_mode, target_batch_id if target_batch_id > 0 else None, run_id),
            )
            if target_batch_id > 0:
                conn.execute("UPDATE import_run_files SET target_batch_id=? WHERE run_id=?", (target_batch_id, run_id))
            conn.commit()
        self._reload_review_lines()
        self.status_var.set(f"تم التحليل بنجاح - Run #{run_id}")

    def _reload_review_lines(self) -> None:
        if not self.run_id:
            return
        self.tree.delete(*self.tree.get_children())
        with get_conn(DB_PATH) as conn:
            lines = conn.execute(
                """
                SELECT l.id, l.source_sheet, l.source_row, l.source_label, l.qty, l.amount, l.mapping_status,
                       l.target_kind, l.target_code, l.payload_json, rf.file_name
                FROM import_run_lines l
                JOIN import_run_files rf ON rf.id=l.run_file_id
                WHERE l.run_id=? AND l.line_kind='candidate' AND l.mapping_status<>'ignored'
                ORDER BY rf.file_name, l.source_sheet, l.source_row, l.id
                """,
                (self.run_id,),
            ).fetchall()
        import json

        for row in lines:
            payload = {}
            try:
                payload = json.loads(str(row["payload_json"] or "{}"))
            except Exception:
                payload = {}
            label_raw = payload.get("source_label_raw") or row["source_label"] or ""
            kind = row["target_kind"] or ""
            if not kind:
                kind = payload.get("side") or ""
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["file_name"],
                    row["source_sheet"],
                    row["source_row"],
                    label_raw,
                    f"{float(row['qty'] or 0):,.2f}",
                    f"{float(row['amount'] or 0):,.2f}",
                    row["mapping_status"],
                    kind,
                    row["target_code"] or "",
                ),
            )

    def _selected_line_id(self) -> int:
        sel = self.tree.selection()
        if not sel:
            return 0
        values = self.tree.item(sel[0], "values")
        if not values:
            return 0
        try:
            return int(values[0])
        except Exception:
            return 0

    def _on_tree_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        self.kind_var.set(str(values[8] or "ignore"))
        self.code_var.set(str(values[9] or ""))
        self.new_name_var.set("")
        self.category_var.set("")
        self.unit_var.set("")
        self.has_qty_var.set(0)

    def _apply_selected_mapping(self) -> None:
        if not self.run_id:
            return
        line_id = self._selected_line_id()
        if line_id <= 0:
            messagebox.showwarning("تنبيه", "اختر سطرًا أولًا.", parent=self)
            return

        kind = self.kind_var.get().strip()
        code = self.code_var.get().strip()
        new_name = self.new_name_var.get().strip()
        edit: dict[str, Any]
        if kind == "ignore" or (not code and not new_name):
            edit = {"line_id": line_id, "action": "ignore", "target_kind": "ignore"}
        elif code:
            edit = {
                "line_id": line_id,
                "action": "existing",
                "target_kind": kind,
                "target_code": code,
                "category": self.category_var.get().strip(),
                "unit": self.unit_var.get().strip(),
                "has_qty": int(self.has_qty_var.get() or 0),
            }
        else:
            edit = {
                "line_id": line_id,
                "action": "new",
                "target_kind": kind,
                "target_name": new_name,
                "category": self.category_var.get().strip(),
                "unit": self.unit_var.get().strip(),
                "has_qty": int(self.has_qty_var.get() or 0),
            }
        apply_mapping_edits(self.run_id, [edit])
        self._reload_review_lines()
        self.status_var.set("تم تحديث التصنيف")

    def _commit_run(self) -> None:
        if not self.run_id:
            messagebox.showwarning("تنبيه", "ابدأ التحليل أولًا.", parent=self)
            return
        batch_mode = self.batch_mode_var.get().strip() or "create"
        merge_mode = self.merge_mode_var.get().strip() or "replace"
        target_batch_id = int(self.target_batch_var.get().strip() or "0")
        try:
            report = commit_run(
                run_id=self.run_id,
                batch_mode=batch_mode,
                merge_mode=merge_mode,
                target_batch_id=target_batch_id if target_batch_id > 0 else None,
            )
        except Exception as exc:
            messagebox.showerror("فشل التنفيذ", str(exc), parent=self)
            self.status_var.set("فشل التنفيذ")
            return
        self.status_var.set(f"تم التنفيذ - الحالة: {report.get('status')}")
        messagebox.showinfo(
            "نتيجة الاستيراد",
            f"الحالة: {report.get('status')}\n"
            f"الملفات الناجحة: {report.get('committed_files', 0)}\n"
            f"الملفات الفاشلة: {report.get('failed_files', 0)}\n"
            f"أنواع جديدة: {len(report.get('created_types', []))}\n"
            f"صفوف متكررة متجاوزة: {report.get('skipped_duplicates', 0)}",
            parent=self,
        )
        self._reload_review_lines()


def open_import_wizard(master: tk.Misc | None = None) -> PoultryImportWizard:
    return PoultryImportWizard(master)
