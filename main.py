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

        ttk.Button(btn_frame, text="➕ 新增账号 (INSERT)", command=lambda: self.mock_action("INSERT")).pack(side=tk.LEFT,
                                                                                                           padx=10)
        ttk.Button(btn_frame, text="✏️ 编辑选中行 (UPDATE)", command=lambda: self.mock_action("UPDATE")).pack(
            side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ 删除选中行 (DELETE)", command=lambda: self.mock_action("DELETE")).pack(
            side=tk.LEFT, padx=10)

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

    def mock_action(self, action_name):
        messagebox.showinfo("提示", f"已连接数据库！下一步我们将实现真实的 {action_name} 逻辑。")


# ==========================================
# --- 3. 程序入口 ---
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FunLearnAdminApp(root)
    root.mainloop()