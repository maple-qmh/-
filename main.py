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
        self.password = 'MapleQMH0317'  # ⚠️ 别忘了修改为你的密码
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
        self.root.title("趣味 Python 学习平台 - 后台管理系统")
        self.root.geometry("800x600")

        self.db = DBManager()  # 实例化数据库引擎

        self.setup_ui()  # 初始化界面布局
        self.load_data_from_db()  # 启动时加载一次数据

    def setup_ui(self):
        """搭建整体 UI 框架与选项卡"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_home = ttk.Frame(self.notebook)
        self.tab_users = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_home, text="📊 首页概况")
        self.notebook.add(self.tab_users, text="👥 学生账号管理")

        # 首页简单占位
        tk.Label(self.tab_home, text="欢迎来到管理系统！这里是首页。", font=("微软雅黑", 16)).pack(pady=50)

        # 重点渲染用户管理页
        self.setup_users_tab()

    def setup_users_tab(self):
        """搭建用户管理页的具体内容"""
        # 1. 顶部查询区域
        search_frame = tk.Frame(self.tab_users)
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(search_frame, text="输入学号或昵称:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=20)  # 变成实例属性
        self.search_entry.pack(side=tk.LEFT, padx=10)

        search_btn = ttk.Button(search_frame, text="🔍 查询 (SELECT)", command=self.real_search)
        search_btn.pack(side=tk.LEFT)

        # 2. 中间数据表格区
        columns = ("user_id", "username", "grade", "reg_date")
        self.tree = ttk.Treeview(self.tab_users, columns=columns, show="headings", height=12)

        self.tree.heading("user_id", text="学号 (ID)")
        self.tree.heading("username", text="学生昵称")
        self.tree.heading("grade", text="所在年级")
        self.tree.heading("reg_date", text="注册时间")

        self.tree.column("user_id", width=100, anchor=tk.CENTER)
        self.tree.column("username", width=150, anchor=tk.CENTER)
        self.tree.column("grade", width=100, anchor=tk.CENTER)
        self.tree.column("reg_date", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # 3. 底部操作按钮区域
        btn_frame = tk.Frame(self.tab_users)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(btn_frame, text="➕ 新增账号 (INSERT)", command=self.open_add_user_window).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="✏️ 编辑选中行 (UPDATE)", command=self.open_edit_user_window).pack(side=tk.LEFT,
                                                                                                      padx=10)
        ttk.Button(btn_frame, text="❌ 删除选中行 (DELETE)", command=self.real_delete).pack(side=tk.LEFT, padx=10)

    # --- 交互逻辑方法 ---
    def real_search(self):
        """触发真实查询"""
        keyword = self.search_entry.get()
        self.load_data_from_db(keyword)

    def load_data_from_db(self, search_kw=""):
        """核心业务逻辑：从 MySQL 拉取数据并更新到 Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = self.db.get_connection()
            with conn.cursor() as cursor:
                if search_kw:
                    sql = "SELECT * FROM Users WHERE username LIKE %s OR user_id LIKE %s"
                    cursor.execute(sql, (f"%{search_kw}%", f"%{search_kw}%"))
                else:
                    sql = "SELECT * FROM Users"
                    cursor.execute(sql)

                results = cursor.fetchall()
                for row in results:
                    self.tree.insert("", tk.END, values=(
                        row['user_id'], row['username'], row['grade'], row['registration_date']
                    ))
        except Exception as e:
            messagebox.showerror("数据库错误", f"获取数据失败:\n{e}")
        finally:
            if 'conn' in locals() and conn.open:
                conn.close()

    def real_delete(self):
        """核心业务逻辑：真实的 DELETE 操作"""
        # 1. 获取用户在表格里选中的那一行
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("操作提示", "请先用鼠标点击选中表格里要删除的某一行！")
            return

        # 2. 提取出选中行的 user_id (学号)
        item = self.tree.item(selected[0])
        user_id = item['values'][0]
        username = item['values'][1]

        # 3. 弹出二次确认框，防止误删
        if messagebox.askyesno("危险操作",
                               f"你确定要将【{username} ({user_id})】从数据库中彻底删除吗？\n注意：与之相关的学习进度也会被级联删除！"):
            try:
                # 4. 连接数据库，执行 DELETE
                conn = self.db.get_connection()
                with conn.cursor() as cursor:
                    sql = "DELETE FROM Users WHERE user_id = %s"
                    cursor.execute(sql, (user_id,))

                # ⚠️ 极其重要：对于增删改操作，必须手动 commit(提交)，否则数据库不会生效！
                conn.commit()

                # 5. 删除成功后，重新从数据库拉取最新数据刷新表格
                self.load_data_from_db()
                messagebox.showinfo("成功", f"学生 {username} 的数据已删除。")

            except Exception as e:
                messagebox.showerror("数据库错误", f"删除失败:\n{e}")
            finally:
                if 'conn' in locals() and conn.open:
                    conn.close()

    def open_add_user_window(self):
        """弹出新增账号表单，并执行真实的 INSERT 逻辑"""
        # 1. 创建一个独立的弹窗 (Toplevel)
        add_win = tk.Toplevel(self.root)
        add_win.title("➕ 新增学生账号")
        add_win.geometry("350x300")
        # 让弹窗拦截所有操作，直到关闭
        add_win.grab_set()

        # 2. 绘制表单输入框
        tk.Label(add_win, text="学号 (例: U1003):").pack(pady=5)
        entry_id = tk.Entry(add_win)
        entry_id.pack()

        tk.Label(add_win, text="学生昵称:").pack(pady=5)
        entry_name = tk.Entry(add_win)
        entry_name.pack()

        tk.Label(add_win, text="登录密码:").pack(pady=5)
        entry_pwd = tk.Entry(add_win, show="*")  # 密码用星号隐藏
        entry_pwd.pack()

        tk.Label(add_win, text="所在年级:").pack(pady=5)
        entry_grade = ttk.Combobox(add_win, values=["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"])
        entry_grade.pack()

        # 3. 定义保存按钮的执行逻辑 (INSERT 操作)
        def save_to_db():
            uid = entry_id.get().strip()
            uname = entry_name.get().strip()
            upwd = entry_pwd.get().strip()
            ugrade = entry_grade.get().strip()

            if not uid or not uname or not upwd:
                messagebox.showwarning("提示", "学号、昵称和密码为必填项！", parent=add_win)
                return

            try:
                conn = self.db.get_connection()
                with conn.cursor() as cursor:
                    # 真实的 INSERT 语句，注意这里用 CURDATE() 自动获取今天作为注册日期
                    sql = "INSERT INTO Users (user_id, username, password, grade, registration_date) VALUES (%s, %s, %s, %s, CURDATE())"
                    cursor.execute(sql, (uid, uname, upwd, ugrade))

                conn.commit()  # 提交入库
                messagebox.showinfo("成功", "新账号已成功存入数据库！", parent=add_win)
                add_win.destroy()  # 关闭弹窗
                self.load_data_from_db()  # 重新拉取数据，刷新界面表格

            except pymysql.err.IntegrityError:
                messagebox.showerror("冲突", f"学号 {uid} 已经存在，请换一个！", parent=add_win)
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}", parent=add_win)
            finally:
                if 'conn' in locals() and conn.open:
                    conn.close()

        # 4. 放置保存按钮
        ttk.Button(add_win, text="💾 确认保存至数据库", command=save_to_db).pack(pady=20)

    def open_edit_user_window(self):
        """弹出编辑窗口，执行 UPDATE 逻辑"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("操作提示", "请先在表格中点击选中一行要编辑的数据！")
            return

        # 提取当前选中的旧数据
        item = self.tree.item(selected[0])
        user_id = item['values'][0]
        old_name = item['values'][1]
        old_grade = item['values'][2]

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"✏️ 修改学生信息 (学号: {user_id})")
        edit_win.geometry("300x200")
        edit_win.grab_set()

        tk.Label(edit_win, text="修改昵称:").pack(pady=5)
        entry_name = tk.Entry(edit_win)
        entry_name.insert(0, old_name)  # 填入旧名字
        entry_name.pack()

        tk.Label(edit_win, text="修改年级:").pack(pady=5)
        entry_grade = ttk.Combobox(edit_win, values=["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"])
        entry_grade.set(old_grade)  # 填入旧年级
        entry_grade.pack()

        def save_update():
            new_name = entry_name.get().strip()
            new_grade = entry_grade.get().strip()
            try:
                conn = self.db.get_connection()
                with conn.cursor() as cursor:
                    sql = "UPDATE Users SET username = %s, grade = %s WHERE user_id = %s"
                    cursor.execute(sql, (new_name, new_grade, user_id))
                conn.commit()
                messagebox.showinfo("成功", "信息修改成功！", parent=edit_win)
                edit_win.destroy()
                self.load_data_from_db()  # 刷新表格
            except Exception as e:
                messagebox.showerror("错误", f"修改失败:\n{e}", parent=edit_win)

        ttk.Button(edit_win, text="💾 保存修改 (UPDATE)", command=save_update).pack(pady=20)


# ==========================================
# --- 3. 程序入口 ---
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FunLearnAdminApp(root)
    root.mainloop()