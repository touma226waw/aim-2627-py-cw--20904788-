# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    """("Q1 hp_ratio：题面 Q1·血量百分比与精度保障")"""

    # 血量百分比，返回 0-100 的 int
    hp_per = int((hp / max_hp) * 100) if max_hp > 0 else 0
    hp_per = max(0, min(100, hp_per))  # 限制在 0-100 范围内
    return hp_per


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    """("Q1 status_report：题面 Q1·电量映射与报告格式")"""

    hp_per = hp_ratio(hp, max_hp)

    if battery >= 60:
        battery_level = "OK"
    elif 20 <= battery < 60:
        battery_level = "WARNING"
    else:
        battery_level = "LOW"

    result = f"{name:<10}|{robot_type:^10}|HP {hp_per:>3}%|BAT {battery:>3}%|{battery_level}"

    return result


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """TODO(Q2)：解析混合格式伤害日志，返回固定契约的统计 dict；
    行格式、去重与统计口径见题面 Q2 规范。"""
    """("Q2 analyze_damage_log：题面 Q2·多源日志解析与统计")"""

    import json

    # 初始化
    starts = {'total': 0,
              "by_armor": {"front": 0, "left": 0, "right": 0},
              "most_hit": None,
              "avg": 0.0}
    id_set = set()
    event_count = 0
    armor_map = {"F": "front", "L": "left", "R": "right"}

    # 跳过不符合格式的行
    for line in lines:
        line = line.strip()
        if not line:
            continue
        elif not line.startswith('{') and not line.startswith(('F', 'L', 'R')):
            continue

    # 分辨 JSON行，传感器行，脏行并累加
        if line.startswith('{'):
            # JSON行分辨
            try:
                data = json.loads(line)
                if type(data) is not dict:
                    continue
                armor = data.get('armor')
                damage = data.get("damage")
                if armor not in ("front", "left", "right"):
                    continue
                if type(damage) is not int or damage <= 0:
                    continue
                if "id" in data:
                    # id去重
                    id_num = data["id"]
                    if id_num in id_set:
                        continue
                    id_set.add(id_num)
                # 累加
                starts['total'] += damage
                starts['by_armor'][armor] += damage
                event_count += 1
            except Exception:
                pass

        elif line.startswith(('F:', 'L:', 'R:')):
            # 传感器行分辨
            parts = line.split(',')
            temporary = []
            valid = True

            for part in parts:
                try:
                    pieces = part.split(':')
                    if len(pieces) != 2:
                        valid = False
                        break
                    armor, damageV = pieces
                except ValueError:
                    valid = False
                    break
                if armor not in ("F", "L", "R"):
                    valid = False
                    break
                if not damageV.isdigit():
                    valid = False
                    break
                damageR = int(damageV)
                if damageR <= 0:
                    valid = False
                    break
                temporary.append((armor, damageR))
            if not valid:
                continue

      # 累加
            for armor, damageR in temporary:
                starts['total'] += damageR
                starts['by_armor'][armor_map[armor]] += damageR
                event_count += 1
        else:
            pass

# 最大受击部位
    if event_count > 0:
        starts["most_hit"] = max(
            starts["by_armor"],
            key=starts["by_armor"].get
        )
    else:
        starts["most_hit"] = None

        # 平均伤害
    if event_count > 0:
        starts["avg"] = round(starts["total"]/event_count, 2)
    else:
        starts["avg"] = 0.0

    return starts

# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------


class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        """("Q3 current_pos.setter：题面 Q3·位置校验三步")"""
        # 位置必须是 tuple 或 list
        if not isinstance(value, (tuple, list)):
            raise TypeError
        # 位置长度必须是 2
        if len(value) != 2:
            raise TypeError
        # 规范化储存
        normal_value = (int(value[0]), int(value[1]))
        self._pos = normal_value

    def move_forward(self):
        """(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        """("Q3 move_forward：题面 Q3·前进、碰撞与断电")"""
        # 检测是否断电
        if self._fuel <= 0:
            return self._pos
        # 坐标与移动后坐标
        # dx or dy 的+—1决定朝向
        x, y = self._pos
        dx, dy = self._facing.delta
        target_x = x + dx
        target_y = y + dy

        # 障碍判断，电量和事件的更新
        if self.is_blocked(target_x, target_y):
            self._collision_count += 1
        else:
            self._pos = (target_x, target_y)
            self._fuel -= 1

        return self._pos

    def turn_left(self):
        """(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        """("Q3 turn_left")"""
        # 字典映射直接改变facing
        left_map = {
            Facing.UP: Facing.LEFT,
            Facing.LEFT: Facing.DOWN,
            Facing.DOWN: Facing.RIGHT,
            Facing.RIGHT: Facing.UP,
        }
        self._facing = left_map[self._facing]
        return self._facing

    def turn_right(self):
        """(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        """("Q3 turn_right")"""
        right_map = {
            Facing.UP: Facing.RIGHT,
            Facing.RIGHT: Facing.DOWN,
            Facing.DOWN: Facing.LEFT,
            Facing.LEFT: Facing.UP,
        }

        self._facing = right_map[self._facing]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """(Q4)：返回下一步应朝向的 Facing；
    候选判定、优先级与回退规则见题面 Q4 规范。"""
    """("Q4 next_step_toward：题面 Q4·贪心策略与回退")"""
    # x,y位终点  x1,y1为起点  x2,y2 and x3,y3均为下一步坐标
    # candi为候选方向
    # 初始化
    x1, y1 = pos
    x, y = target
    Manhattan1 = abs(x1 - x) + abs(y1 - y)
    candi = []

    # 遍历方向，找候选方向
    for facing in (Facing.UP, Facing.DOWN, Facing.LEFT, Facing.RIGHT):
        dx, dy = facing.delta
        candi_pos = (x1+dx, y1+dy)
        if candi_pos in obstacles:
            continue
        Manhattan2 = abs(x1 + dx - x) + abs(y1 + dy - y)
        if Manhattan1 > Manhattan2:
            candi.append(facing)
    if not candi:
        return current_facing

    # 轴向偏好
    x_gap = abs(x1 - x)
    y_gap = abs(y1 - y)
    if x_gap > y_gap:
        prefer = (Facing.RIGHT, Facing.LEFT)
    elif x_gap < y_gap:
        prefer = (Facing.UP, Facing.DOWN)
    else:
        return candi[0]

    # 输出贪心方向结果
    for result in prefer:
        if result in candi:
            return result
    return candi[0]

# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------


class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    """(Q5)：纯函数决策，返回 (action: str, new_state: SentryState)；
    sensor 字段契约、R1-R7 规则表与非法输入处理见题面 Q5 规范。"""
    """("Q5 decide：题面 Q5·决策规则表 R1-R7")"""

    required = (
        "enemy_frames",
        "enemy_dist",
        "robot_type",
        "max_hp",
    )
# 检查sensor字段是否合法
# 是否字典
    if not isinstance(sensor, dict):
        raise ValueError
    for key in required:
        if key not in sensor:
            raise ValueError
# 是否枚举
    if not isinstance(state, SentryState):
        raise ValueError
# 接受tuple和list
    frames = sensor["enemy_frames"]
    if not isinstance(frames, (tuple, list)):
        raise ValueError
# 敌检历史长度1-6
    if not 1 <= len(frames) <= 6:
        raise ValueError

# 读取初始条件
    frames = sensor["enemy_frames"]
    distance = sensor["enemy_dist"]
    robot_type = sensor["robot_type"]
    max_hp = sensor["max_hp"]
    hp_pct = hp_ratio(hp, max_hp)
    visible = bool(frames[-1])

# R1
    if hp_pct <= 30:
        return ("RETREAT", SentryState.RETREAT)
    else:
        pass
# R2
    if state == SentryState.RETREAT:
        if hp_pct > 30:
            return ("RETURN", SentryState.RETURN)
        else:
            return ("RETREAT", SentryState.RETREAT)
# R3
    if state == SentryState.RETURN:
        return ("MOVE_BASE", SentryState.PATROL)
# R4
    if state == SentryState.ENGAGE and bool(sensor["enemy_frames"][-1]) is True:
        if distance <= 3:
            return ("SHOOT", SentryState.ENGAGE)
        else:
            if robot_type == "HERO":
                return ("MOVE_RIGHT", SentryState.ENGAGE)
            elif robot_type == "INFANTRY":
                return ("MOVE_LEFT", SentryState.ENGAGE)
            else:
                pass
# R5
    if state == SentryState.ENGAGE and bool(sensor["enemy_frames"][-1]) is not True:
        if bool(sensor["enemy_frames"][-2]) is True:
            return ("HOLD_FIRE", SentryState.ENGAGE)
        elif bool(sensor["enemy_frames"][-2]) is False:
            return ("SCAN", SentryState.SUSPECT)
# R6
    if state in (SentryState.PATROL, SentryState.SUSPECT) and bool(sensor["enemy_frames"][-1]) is True:
        if len(sensor["enemy_frames"]) >= 2 and bool(sensor["enemy_frames"][-2]) is True:
            if sensor["enemy_dist"] <= 3:
                return ("SHOOT", SentryState.ENGAGE)
            else:
                if sensor["robot_type"] == "HERO":
                    return ("MOVE_RIGHT", SentryState.ENGAGE)
                elif sensor["robot_type"] == "INFANTRY":
                    return ("MOVE_LEFT", SentryState.ENGAGE)
                else:
                    pass
        else:
            return ("SCAN", SentryState.SUSPECT)
# R7
    if state in (SentryState.PATROL, SentryState.SUSPECT) and bool(sensor["enemy_frames"][-1]) is False:
        if state == SentryState.PATROL:
            return ("PATROL_MOVE", SentryState.PATROL)
        else:
            return ("SCAN", SentryState.SUSPECT)

# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------


def run_patrol(grid, max_steps=500):
    """(Q6)：sense → decide → act 主循环；
    # 循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    """("Q6 run_patrol：题面 Q6·主循环与统计契约")"""
# 初始化
    steps = 0
    visited = {grid.current_pos}
    cx, cy = grid.current_pos
    ex, ey = grid.enemy_pos
    pre_dist = abs(cx - ex) + abs(cy - ey)
    cur_dist = abs(cx - ex) + abs(cy - ey)
    no_progress_count = 0
    escape_mode = False
    left_of = {
        Facing.UP: Facing.LEFT,
        Facing.LEFT: Facing.DOWN,
        Facing.DOWN: Facing.RIGHT,
        Facing.RIGHT: Facing.UP,
    }
    right_of = {
        Facing.UP: Facing.RIGHT,
        Facing.LEFT: Facing.UP,
        Facing.DOWN: Facing.LEFT,
        Facing.RIGHT: Facing.DOWN, }
    entry_dist = 0
# 开始巡逻
    while steps < max_steps and grid.fuel > 0 and not grid.found_enemy:
        # 困境下一步方向,优先左手规则
        if escape_mode:

            # 左手规则如下，左前右后 escape_hand = "L"
            if escape_hand == "L":
                left = left_of[grid.facing]
                front = grid.facing
                right = {v: k for k, v in left_of.items()}[grid.facing]
                back = {
                    Facing.UP: Facing.DOWN,
                    Facing.DOWN: Facing.UP,
                    Facing.LEFT: Facing.RIGHT,
                    Facing.RIGHT: Facing.LEFT,
                }[grid.facing]
                dx, dy = left.delta
                left_cell = (cx + dx, cy + dy)
                dx, dy = front.delta
                front_cell = (cx + dx, cy + dy)
                dx, dy = right.delta
                right_cell = (cx + dx, cy + dy)
                if not grid.is_blocked(left_cell[0], left_cell[1]):
                    desired_facing = left
                elif not grid.is_blocked(front_cell[0], front_cell[1]):
                    desired_facing = front
                elif not grid.is_blocked(right_cell[0], right_cell[1]):
                    desired_facing = right
                else:
                    desired_facing = back
            elif escape_hand == "R":
                right = right_of[grid.facing]
                front = grid.facing
                left = {v: k for k, v in left_of.items()}[grid.facing]
                back = {
                    Facing.UP: Facing.DOWN,
                    Facing.DOWN: Facing.UP,
                    Facing.LEFT: Facing.RIGHT,
                    Facing.RIGHT: Facing.LEFT,
                }[grid.facing]
                dx, dy = right.delta
                right_cell = (cx + dx, cy + dy)
                dx, dy = front.delta
                front_cell = (cx + dx, cy + dy)
                dx, dy = left.delta
                left_cell = (cx + dx, cy + dy)
                if not grid.is_blocked(right_cell[0], right_cell[1]):
                    desired_facing = right
                elif not grid.is_blocked(front_cell[0], front_cell[1]):
                    desired_facing = front
                elif not grid.is_blocked(left_cell[0], left_cell[1]):
                    desired_facing = left
                else:
                    desired_facing = back
# 贪心下一步方向
# 调用next...函数，传入了四个参数计算下一步期望方向
        else:
            desired_facing = next_step_toward(
                grid.current_pos,
                grid.enemy_pos,
                grid.obstacles,
                grid.facing,
            )
# 一直右转直到与期望方向重合
        while grid.facing is not desired_facing:
            grid.turn_right()
# 前进1并记录更新历史
        grid.move_forward()
        cx, cy = grid.current_pos
        cur_dist = abs(cx - ex) + abs(cy - ey)
        steps += 1
        visited.add(grid.current_pos)
# 判断是否是困境
        if cur_dist < pre_dist:
            # 有进展，进入贪心
            no_progress_count = 0
        else:
            # 没有进展，开启三步判定
            no_progress_count += 1
        pre_dist = cur_dist
# 判定陷入困境，开始脱困（优先左手规则）
        if no_progress_count >= 2 and not escape_mode:
            escape_mode = True
            entry_dist = cur_dist
            try_steps = 0
            escape_hand = "L"
# 判断是否脱困
    # 成功脱困
        if escape_mode:
            try_steps += 1
            if entry_dist > cur_dist:
                escape_mode = False
                no_progress_count = 0
                pre_dist = cur_dist
    # 左手5步无法脱困，切换右手
            elif try_steps > 4:
                escape_hand = "R" if escape_hand == "L" else "L"
                try_steps = 0

    return {
        "steps": steps,
        "collisions": grid.collision_count,
        "visited_count": len(visited),
        "found_enemy": grid.found_enemy,
        "success": grid.found_enemy,
    }


def report_to_json(stats):
    """(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    """("Q6 report_to_json：题面 Q6·报告序列化")"""
    return json.dumps(stats, sort_keys=True)


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    raise NotImplementedError("Bonus bfs_path_length")


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
