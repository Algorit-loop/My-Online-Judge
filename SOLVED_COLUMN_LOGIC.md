# Cơ Chế "Solved" Column trong Trang Problem List

## 📋 Câu Hỏi

Tại trang `http://localhost:8080/problems/`, cột `<th class="solved">` được lấy như thế nào?  
Có phải là lấy submission có kết quả tốt nhất của user không?

## ✅ Câu Trả Lời

**CÓ** - Hệ thống lấy những bài mà user đã có ít nhất 1 submission với kết quả **AC (Accepted)** và **tất cả test case đều passed** (`case_points >= case_total`).

---

## 🔄 Luồng Dữ Liệu

```
User truy cập /problems/
       ↓
View: ProblemList (Django)
       ├─ Call: self.get_completed_problems()
       ├─ Call: self.get_attempted_problems()
       ↓
SolvedProblemMixin (class mixin)
       ├─ get_completed_problems() → user_completed_ids(profile)
       ├─ get_attempted_problems() → user_attempted_ids(profile)
       ↓
Utility function (judge/utils/problems.py)
       ├─ user_completed_ids(profile) ← Query DB + Cache
       ├─ user_attempted_ids(profile) ← Query DB + Cache
       ↓
Template Context (problem/list.html)
       ├─ completed_problem_ids = {...}
       ├─ attempted_problems = {...}
       ↓
Template Rendering (Jinja2)
       ├─ Kiểm tra problem.id in completed_problem_ids
       ├─ Kiểm tra problem.id in attempted_problems
       ├─ Render icon tương ứng
       ↓
Display HTML
       └─ ✓ AC (green check)
       └─ ✗ Attempted (red sad face)
       └─ (empty) Not solved
```

---

## 📍 Code Implementation

### 1️⃣ View Layer - `judge/views/problem.py`

#### Mixin Class (line 82-104)

```python
class SolvedProblemMixin(object):
    """Lớp dùng chung cho các view cần biết bài đã solved hay chưa"""
    
    def get_completed_problems(self):
        """Trả về set các problem ID mà user đã AC"""
        return user_completed_ids(self.profile) if self.profile is not None else ()

    def get_attempted_problems(self):
        """Trả về set các problem ID mà user đã từng submit"""
        return user_attempted_ids(self.profile) if self.profile is not None else ()

    @cached_property
    def profile(self):
        """Lấy profile của user hiện tại"""
        if not self.request.user.is_authenticated:
            return None
        return self.request.profile
```

#### ProblemList View (line 660-665)

```python
class ProblemList(SolvedProblemMixin, ..., ListView):
    """View hiển thị danh sách bài tập"""
    
    def get_context_data(self, **kwargs):
        context = super(ProblemList, self).get_context_data(**kwargs)
        # ... other code ...
        context['completed_problem_ids'] = self.get_completed_problems()  # ← Set các bài AC
        context['attempted_problems'] = self.get_attempted_problems()      # ← Set các bài attempted
        # ... return context ...
        return context
```

---

### 2️⃣ Utility Layer - `judge/utils/problems.py`

#### `user_completed_ids(profile)` - Line 33-39

```python
def user_completed_ids(profile):
    """
    Trả về set các problem ID mà user đã fully solve (AC với 100% test case)
    
    Args:
        profile: UserProfile object
    
    Returns:
        set: Tập hợp problem ID user đã AC
    """
    key = 'user_complete:%d' % profile.id
    result = cache.get(key)  # ← Kiểm tra cache trước
    
    if result is None:
        # Query cơ sở dữ liệu nếu không có cache
        result = set(
            Submission.objects.filter(
                user=profile,                          # ← User này
                result='AC',                           # ← Kết quả AC (Accepted)
                case_points__gte=F('case_total')       # ← Tất cả test case pass
            )
            .values_list('problem_id', flat=True)
            .distinct()
        )
        cache.set(key, result, 86400)  # ← Lưu cache 1 ngày
    
    return result
```

**Điều kiện gọi submission là "Completed":**
- ✓ `result = 'AC'` (Kết quả là Accepted)
- ✓ `case_points >= case_total` (Điểm test = Tổng điểm test)
- ✓ Bất kỳ submission nào thỏa cả 2 điều kiện

---

#### `user_attempted_ids(profile)` - Line 52-58

```python
def user_attempted_ids(profile):
    """
    Trả về set các problem ID mà user đã từng submit (không cần AC)
    
    Args:
        profile: UserProfile object
    
    Returns:
        set: Tập hợp problem ID user đã attempt
    """
    key = 'user_attempted:%s' % profile.id
    result = cache.get(key)  # ← Kiểm tra cache
    
    if result is None:
        # Query: Tất cả submission của user (bất kỳ kết quả gì)
        result = set(
            profile.submission_set
            .values_list('problem_id', flat=True)
            .distinct()
        )
        cache.set(key, result, 86400)  # ← Lưu cache 1 ngày
    
    return result
```

**Điều kiện gọi submission là "Attempted":**
- ✓ Bất kỳ submission nào từ user (AC, WA, CE, TLE, v.v.)
- ✓ Chỉ cần tồn tại ít nhất 1 submission

---

### 3️⃣ Template Layer - `problem/list.html`

#### HTML/Jinja2 Code (line 151-175)

```html
{% for problem in problems %}
    <tr>
        {% if request.user.is_authenticated %}
            <!-- Cột "Solved" -->
            {% if problem.id in completed_problem_ids %}
                <!-- User đã AC bài này -->
                <td class="solved" solved="1">
                    <a href="{{ url('user_submissions', problem.code, request.user.username) }}">
                        {% if problem.is_public %}
                            <i class="solved-problem-color fa fa-check-circle"></i>  <!-- ✓ Green -->
                        {% else %}
                            <i class="solved-problem-color fa fa-lock"></i>  <!-- 🔒 Locked -->
                        {% endif %}
                    </a>
                </td>
            
            {% elif problem.id in attempted_problems %}
                <!-- User đã attempt nhưng chưa AC -->
                <td class="solved" solved="0">
                    <a href="{{ url('user_submissions', problem.code, request.user.username) }}">
                        {% if problem.is_public %}
                            <i class="attempted-problem-color fa fa-frown-o"></i>  <!-- ✗ Red -->
                        {% else %}
                            <i class="attempted-problem-color fa fa-lock"></i>  <!-- 🔒 Locked -->
                        {% endif %}
                    </a>
                </td>
            
            {% else %}
                <!-- User chưa attempt -->
                <td class="solved" solved="-1">
                    {% if problem.is_public %}
                        <i class="unsolved-problem-color fa"></i>  <!-- (empty) Gray -->
                    {% else %}
                        <i class="unsolved-problem-color fa fa-lock"></i>  <!-- 🔒 Locked -->
                    {% endif %}
                </td>
            {% endif %}
        {% endif %}
        
        <!-- ... other columns (code, name, category, etc.) ... -->
    </tr>
{% endfor %}
```

---

## 🗄️ Database Schema (Submission Model)

```sql
-- Bảng Submission
CREATE TABLE judge_submission (
    id INT PRIMARY KEY,
    user_id INT,                    -- FK đến Profile
    problem_id INT,                 -- FK đến Problem
    result VARCHAR(10),             -- 'AC', 'WA', 'CE', 'TLE', 'MLE', ...
    case_points INT,                -- Tổng điểm test đạt được
    case_total INT,                 -- Tổng điểm test
    ...
);

-- Example:
-- User 1 submit problem "aplusb":
-- id | user_id | problem_id | result | case_points | case_total
-- 1  | 1       | 1          | AC     | 100         | 100          ← Completed ✓
-- 2  | 1       | 2          | WA     | 50          | 100          ← Attempted ✗
-- 3  | 1       | 3          | CE     | 0           | 100          ← Attempted ✗
-- (4 | 1       | 4          | -      | -           | -)           ← Not attempted
```

---

## 💾 Caching Strategy

**Cache Key Format:**
```
user_complete:<user_id>     # Ví dụ: user_complete:42
user_attempted:<user_id>    # Ví dụ: user_attempted:42
```

**Cache Duration:** 86400 giây = 1 ngày

**Cache Invalidation:**
- Cache sẽ hết hạn sau 1 ngày
- Khi user submit bài mới, cache được xóa tự động (via Celery tasks)

---

## 🔍 Ví Dụ Thực Tế

### Scenario: User johndoe nộp 3 bài

```
User: johndoe (ID=42)

1. Submit problem "aplusb" (ID=1)
   Result: AC, 100/100 points ✓
   
2. Submit problem "sorting" (ID=2)
   Result: WA, 50/100 points ✗
   
3. Submit problem "graph" (ID=3)
   Result: CE, 0/100 points ✗
   
4. Problem "math" (ID=4)
   No submission yet
```

### Khi johndoe truy cập `/problems/`:

```python
# Query được thực thi:

# 1. Completed problems:
SELECT DISTINCT problem_id FROM judge_submission
WHERE user_id=42 AND result='AC' AND case_points >= case_total
# Result: {1}

# 2. Attempted problems:
SELECT DISTINCT problem_id FROM judge_submission_user=42
# Result: {1, 2, 3}
```

### Template rendering:

| Problem | Status | Icon | Display |
|---------|--------|------|---------|
| aplusb (1) | completed | ✓ | Green checkmark |
| sorting (2) | attempted | ✗ | Red sad face |
| graph (3) | attempted | ✗ | Red sad face |
| math (4) | none | - | Gray empty |

---

## 📊 Performance Notes

| Operation | Complexity | Cache |
|-----------|-----------|-------|
| Query completed problems | O(n) | 1 day |
| Query attempted problems | O(n) | 1 day |
| Render 100 problems | O(100) + O(1) cache lookups | Redis |
| Update cache on new submission | O(1) | Async Celery task |

**Optimization**: Django cache (Redis) lưu từng user riêng biệt, nên không blocking.

---

## 🎯 Kết Luận

| Câu Hỏi | Trả Lời |
|--------|--------|
| **Cách lấy "Solved" column?** | Query `Submission` table theo user + filter `result='AC'` + `case_points >= case_total` |
| **Là best result?** | Không - bất kỳ AC submission nào đều tính |
| **Logic ở đâu?** | [judge/utils/problems.py](judge/utils/problems.py) - `user_completed_ids()` |
| **Cache được dùng?** | Có - Redis 1 ngày |
| **Performance?** | Tốt - query tối ưu + cache |

---

## 📂 File Liên Quan

- [judge/views/problem.py#L82-L104](judge/views/problem.py#L82-L104) - SolvedProblemMixin
- [judge/views/problem.py#L660-L665](judge/views/problem.py#L660-L665) - ProblemList.get_context_data()
- [judge/utils/problems.py#L33-L58](judge/utils/problems.py#L33-L58) - user_completed_ids() + user_attempted_ids()
- [templates/problem/list.html#L151-L175](templates/problem/list.html#L151-L175) - Template rendering
