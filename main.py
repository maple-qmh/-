import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pymysql


# ==========================================
# --- 1. 数据库连接管理器 ---
# ==========================================
class DBManager:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'MapleQMH0317'  # 保持你的密码不变
        self.database = 'student_fun_learn'

    def get_connection(self):
        return pymysql.connect(
            host=self.host, user=self.user, password=self.password,
            database=self.database, charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )


# ==========================================
# --- 2. 界面应用主类 ---
# ==========================================
class FunLearnAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fun Learn 趣味 Python - 终极后台管理系统 (5表联动版)")
        self.root.geometry("950x700")

        self.db = DBManager()
        self.setup_ui()

        # 启动时拉取所有表数据
        self.refresh_all_data()

    def refresh_all_data(self):
        self.load_users()
        self.load_categories()
        self.load_courses()
        self.load_progress()
        self.load_logs()

    def write_log(self, user_id, action):
        """记录操作日志的核心辅助函数"""
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                # user_id 如果没有可以直接传 None
                cur.execute("INSERT INTO operation_log (user_id, action) VALUES (%s, %s)", (user_id, action))
            conn.commit()
            self.load_logs()  # 刷新日志界面
        except Exception as e:
            print(f"日志记录失败: {e}")
        finally:
            if 'conn' in locals() and conn.open: conn.close()

    def setup_ui(self):
        """搭建包含 5 个选项卡的整体 UI 框架"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_users = ttk.Frame(self.notebook)
        self.tab_category = ttk.Frame(self.notebook)
        self.tab_courses = ttk.Frame(self.notebook)
        self.tab_progress = ttk.Frame(self.notebook)
        self.tab_logs = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_users, text="👥 账号管理 (users)")
        self.notebook.add(self.tab_category, text="📑 分类管理 (category)")
        self.notebook.add(self.tab_courses, text="📚 关卡管理 (courses)")
        self.notebook.add(self.tab_progress, text="📈 进度管理 (progress)")
        self.notebook.add(self.tab_logs, text="🛡️ 系统日志 (log)")

        self.setup_users_tab()
        self.setup_category_tab()
        self.setup_courses_tab()
        self.setup_progress_tab()
        self.setup_logs_tab()

    # ==========================================
    # --- 模块 A: 学生账号管理 (users) ---
    # ==========================================
    def setup_users_tab(self):
        btn_frame = tk.Frame(self.tab_users);
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(btn_frame, text="➕ 新增账号", command=self.open_add_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ 删除选中", command=self.delete_user).pack(side=tk.LEFT, padx=10)

        cols = ("user_id", "username", "grade", "status", "reg_date")
        self.user_tree = ttk.Treeview(self.tab_users, columns=cols, show="headings", height=15)
        self.user_tree.heading("user_id", text="学号");
        self.user_tree.heading("username", text="昵称")
        self.user_tree.heading("grade", text="年级");
        self.user_tree.heading("status", text="状态(1正常/0禁用)")
        self.user_tree.heading("reg_date", text="注册时间")
        self.user_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def load_users(self):
        for item in self.user_tree.get_children(): self.user_tree.delete(item)
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            for row in cur.fetchall():
                self.user_tree.insert("", tk.END, values=(row['user_id'], row['username'], row['grade'], row['status'],
                                                          row['registration_date']))
            conn.close()
        except Exception:
            pass

    def open_add_user(self):
        win = tk.Toplevel(self.root);
        win.title("新增学生");
        win.geometry("300x250");
        win.grab_set()
        tk.Label(win, text="学号 (如U002):").pack();
        en_id = tk.Entry(win);
        en_id.pack()
        tk.Label(win, text="昵称:").pack();
        en_name = tk.Entry(win);
        en_name.pack()
        tk.Label(win, text="密码:").pack();
        en_pwd = tk.Entry(win, show="*");
        en_pwd.pack()
        tk.Label(win, text="年级:").pack();
        cb_grade = ttk.Combobox(win, values=["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]);
        cb_grade.pack()

        def save():
            try:
                conn = self.db.get_connection()
                with conn.cursor() as cur:
                    # 状态和时间使用数据库默认值
                    cur.execute("INSERT INTO users (user_id, username, password, grade) VALUES (%s, %s, %s, %s)",
                                (en_id.get(), en_name.get(), en_pwd.get(), cb_grade.get()))
                conn.commit()
                self.write_log(None, f"管理员新增了学生账号: {en_name.get()}")
                win.destroy();
                self.load_users()
            except Exception as e:
                messagebox.showerror("约束拦截", f"添加失败，违反数据库规则:\n{e}", parent=win)
            finally:
                if 'conn' in locals() and conn.open: conn.close()

        ttk.Button(win, text="保存", command=save).pack(pady=10)

    def delete_user(self):
        sel = self.user_tree.selection()
        if not sel or not messagebox.askyesno("警告", "确定删除该用户吗？相关进度将级联删除！"): return
        uid = self.user_tree.item(sel[0])['values'][0];
        uname = self.user_tree.item(sel[0])['values'][1]
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE user_id=%s", (uid,))
            conn.commit()
            self.write_log(None, f"管理员删除了学生账号: {uname}")
            self.refresh_all_data()
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")
        finally:
            if 'conn' in locals() and conn.open: conn.close()

    # ==========================================
    # --- 模块 B: 分类管理 (category) ---
    # ==========================================
    def setup_category_tab(self):
        btn_frame = tk.Frame(self.tab_category);
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(btn_frame, text="➕ 新增分类", command=self.open_add_category).pack(side=tk.LEFT)

        cols = ("cid", "cname", "sort")
        self.cat_tree = ttk.Treeview(self.tab_category, columns=cols, show="headings", height=10)
        self.cat_tree.heading("cid", text="分类ID");
        self.cat_tree.heading("cname", text="分类名称");
        self.cat_tree.heading("sort", text="排序权重")
        self.cat_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def load_categories(self):
        for item in self.cat_tree.get_children(): self.cat_tree.delete(item)
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            cur.execute("SELECT * FROM category ORDER BY sort_no DESC")
            for row in cur.fetchall():
                self.cat_tree.insert("", tk.END, values=(row['category_id'], row['category_name'], row['sort_no']))
            conn.close()
        except Exception:
            pass

    def open_add_category(self):
        win = tk.Toplevel(self.root);
        win.title("新增分类");
        win.geometry("300x150");
        win.grab_set()
        tk.Label(win, text="分类名称:").pack(pady=5);
        en_name = tk.Entry(win);
        en_name.pack()
        tk.Label(win, text="排序权重(越大越靠前):").pack(pady=5);
        en_sort = tk.Entry(win);
        en_sort.insert(0, "0");
        en_sort.pack()

        def save():
            try:
                conn = self.db.get_connection()
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO category (category_name, sort_no) VALUES (%s, %s)",
                                (en_name.get(), en_sort.get()))
                conn.commit();
                self.write_log(None, f"新增了课程分类: {en_name.get()}");
                win.destroy();
                self.load_categories()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{e}", parent=win)

        ttk.Button(win, text="保存", command=save).pack(pady=10)

    # ==========================================
    # --- 模块 C: 关卡管理 (courses) ---
    # ==========================================
    def setup_courses_tab(self):
        btn_frame = tk.Frame(self.tab_courses);
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(btn_frame, text="➕ 新增关卡", command=self.open_add_course).pack(side=tk.LEFT)

        cols = ("id", "name", "cat", "diff", "price")
        self.course_tree = ttk.Treeview(self.tab_courses, columns=cols, show="headings", height=15)
        self.course_tree.heading("id", text="ID");
        self.course_tree.heading("name", text="关卡名称")
        self.course_tree.heading("cat", text="所属分类");
        self.course_tree.heading("diff", text="难度");
        self.course_tree.heading("price", text="解锁价格")
        self.course_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def load_courses(self):
        for item in self.course_tree.get_children(): self.course_tree.delete(item)
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            # 联查分类名称
            sql = "SELECT c.course_id, c.course_name, cat.category_name, c.difficulty, c.price FROM courses c LEFT JOIN category cat ON c.category_id = cat.category_id"
            cur.execute(sql)
            for row in cur.fetchall():
                self.course_tree.insert("", tk.END, values=(row['course_id'], row['course_name'], row['category_name'],
                                                            row['difficulty'], row['price']))
            conn.close()
        except Exception:
            pass

    def open_add_course(self):
        win = tk.Toplevel(self.root);
        win.title("新增关卡");
        win.geometry("300x300");
        win.grab_set()

        # 获取现有的分类供选择
        cats = [];
        cat_ids = {}
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            cur.execute("SELECT category_id, category_name FROM category")
            for row in cur.fetchall():
                name = row['category_name']
                cats.append(name);
                cat_ids[name] = row['category_id']
            conn.close()
        except:
            pass

        tk.Label(win, text="关卡名称:").pack();
        en_name = tk.Entry(win);
        en_name.pack()
        tk.Label(win, text="所属分类 (外键约束):").pack();
        cb_cat = ttk.Combobox(win, values=cats);
        cb_cat.pack()
        tk.Label(win, text="难度:").pack();
        cb_diff = ttk.Combobox(win, values=["简单", "中等", "困难"]);
        cb_diff.pack()
        tk.Label(win, text="价格 (不能为负数):").pack();
        en_price = tk.Entry(win);
        en_price.insert(0, "0.00");
        en_price.pack()

        def save():
            cid = cat_ids.get(cb_cat.get())
            try:
                conn = self.db.get_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO courses (course_name, category_id, difficulty, price) VALUES (%s, %s, %s, %s)",
                        (en_name.get(), cid, cb_diff.get(), en_price.get()))
                conn.commit();
                self.write_log(None, f"新增了关卡: {en_name.get()}");
                win.destroy();
                self.load_courses()
            except Exception as e:
                messagebox.showerror("约束拦截", f"添加失败，违反规则:\n{e}", parent=win)

        ttk.Button(win, text="保存", command=save).pack(pady=15)

    # ==========================================
    # --- 模块 D: 进度管理 (progress) ---
    # ==========================================
    def setup_progress_tab(self):
        btn_frame = tk.Frame(self.tab_progress);
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(btn_frame, text="➕ 分配关卡记录", command=self.open_add_progress).pack(side=tk.LEFT)

        cols = ("rid", "uname", "cname", "status", "score")
        self.prog_tree = ttk.Treeview(self.tab_progress, columns=cols, show="headings", height=15)
        self.prog_tree.heading("rid", text="记录ID");
        self.prog_tree.heading("uname", text="学生姓名")
        self.prog_tree.heading("cname", text="关卡名称");
        self.prog_tree.heading("status", text="状态")
        self.prog_tree.heading("score", text="得分 (0-100)")
        self.prog_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def load_progress(self):
        for item in self.prog_tree.get_children(): self.prog_tree.delete(item)
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            sql = "SELECT p.record_id, u.username, c.course_name, p.status, p.score FROM progress p JOIN users u ON p.user_id = u.user_id JOIN courses c ON p.course_id = c.course_id"
            cur.execute(sql)
            for row in cur.fetchall():
                self.prog_tree.insert("", tk.END,
                                      values=(row['record_id'], row['username'], row['course_name'], row['status'],
                                              row['score']))
            conn.close()
        except Exception:
            pass

    def open_add_progress(self):
        win = tk.Toplevel(self.root);
        win.title("分配进度");
        win.geometry("350x250");
        win.grab_set()
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            cur.execute("SELECT user_id, username FROM users");
            users = cur.fetchall()
            cur.execute("SELECT course_id, course_name FROM courses");
            courses = cur.fetchall()
            conn.close()
        except:
            return

        tk.Label(win, text="选择学生:").pack(pady=5);
        cb_user = ttk.Combobox(win, values=[f"{u['user_id']}-{u['username']}" for u in users], width=30);
        cb_user.pack()
        tk.Label(win, text="选择关卡:").pack(pady=5);
        cb_course = ttk.Combobox(win, values=[f"{c['course_id']}-{c['course_name']}" for c in courses], width=30);
        cb_course.pack()
        tk.Label(win, text="初始得分:").pack();
        en_score = tk.Entry(win);
        en_score.insert(0, "0");
        en_score.pack()

        def save():
            u_id = cb_user.get().split('-')[0];
            c_id = cb_course.get().split('-')[0]
            try:
                conn = self.db.get_connection()
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO progress (user_id, course_id, score) VALUES (%s, %s, %s)",
                                (u_id, c_id, en_score.get()))
                conn.commit();
                self.write_log(u_id, "被分配了新关卡");
                win.destroy();
                self.load_progress()
            except Exception as e:
                messagebox.showerror("约束拦截", f"添加失败，违反规则:\n{e}", parent=win)

        ttk.Button(win, text="分配", command=save).pack(pady=10)

    # ==========================================
    # --- 模块 E: 操作日志 (operation_log) ---
    # ==========================================
    def setup_logs_tab(self):
        tk.Label(self.tab_logs, text="⚠️ 以下日志由系统底层触发自动记录，无法手动修改。", fg="red").pack(pady=5)
        cols = ("log_id", "uid", "action", "time")
        self.log_tree = ttk.Treeview(self.tab_logs, columns=cols, show="headings", height=15)
        self.log_tree.heading("log_id", text="日志ID");
        self.log_tree.heading("uid", text="涉及学号")
        self.log_tree.heading("action", text="操作记录");
        self.log_tree.heading("time", text="发生时间")
        self.log_tree.column("action", width=400)
        self.log_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def load_logs(self):
        for item in self.log_tree.get_children(): self.log_tree.delete(item)
        try:
            conn = self.db.get_connection();
            cur = conn.cursor()
            cur.execute("SELECT * FROM operation_log ORDER BY create_time DESC")
            for row in cur.fetchall():
                self.log_tree.insert("", tk.END,
                                     values=(row['log_id'], row['user_id'], row['action'], row['create_time']))
            conn.close()
        except Exception:
            pass


# ==========================================
# --- 3. 程序入口 ---
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FunLearnAdminApp(root)
    root.mainloop()