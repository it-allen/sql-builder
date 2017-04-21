# sql-builder
A tool to build sql statement, avoiding to write SQLs directly. 


## Install
```sh
pip install sql-builder
```

## Examples
```python
# Given 5 tables as following:
# 
#    class: id, name
#    student: id, name, class_id(class:id), age
#    student_snapshot: id, name, class_id, age
#    teacher: id, name
#    teach: teacher_id(teacher:id), class_id(class:id)
import sql_builder


student = Table("student").as_("s")
ss = Table("student_snapshot").as_("snapshot")
class_ = Table("class").as_("c")
teacher = Table("teacher")
teach = Table("teach").as_("ss")

print(student.select(student.builtin_all)[4:10].sql())
print(student.select(student.builtin_all, student.age.max_("max_age")).sql())
print(student.select(student.builtin_all, student.age.min_("min_age")).sql())
print(student.select(student.id.count("student_count")).sql())
print(student.select().sql())

print(Select(tables=student.join(class_, (student.class_id == class_.id) & (student.age == 20))).asc(class_.name).sql("?"))
print(Select(tables=teacher.join(teach,
                                 teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id),
             where=(class_.id == '123123'), fields=[teacher.builtin_all]).sql())
print(Select(tables=teacher.join(teach,
                                 teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id)).where(
    class_.id == None).select(teacher.builtin_all).sql())
print("=" * 20)
print(Insert(student, student.id, 1, student.name, "学生a", student.class_id, "21321").on_duplicate_key_fields(
    student.name, "学生a").sql())
print(student.insert(id=1, name="学生a", class_id="21321").on_duplicate_key_fields(name="学生a").add_fields(age=20).sql())

sub = Select(student).where(student.name == 'test').select(
    student.id, student.name, student.class_id, student.age).as_table("old_student")
print(InsertFromSelect(ss, [ss.id, ss.name, ss.class_id, ss.age], sub).sql())

print(student.update(student.name, "学生").where(student.id == 1).sql())
print(student.update(name="学生").add_fields(age=20).where(student.id == 1).sql())
print(Delete(table=student).where(student.id == 1).sql())
print(Delete(table=teacher).where(teacher.id.in_(
    Select(tables=teach.join(teacher, teach.teacher_id == teacher.id)).select(teacher.id).where((teach.class_id == 2) & (teacher.deleted == 0)))).sql())

```
