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

Select(tables=student, fields=[student.builtin_all, student.age.max_()]).sql
# ('SELECT `s`.*, MAX(`s`.`age`) FROM `student` AS `s`', [])

Select(tables=student).select(student.builtin_all, student.age.max_("max_age"))[0:4].sql
# ('SELECT `s`.*, MAX(`s`.`age`) AS `max_age` FROM `student` AS `s` LIMIT 0, 4', [])

Select(tables=student.join(class_, student.class_id == class_.id)).sql
# ('SELECT * FROM `student` AS `s` INNER JOIN `class` AS `c` ON `s`.`class_id` = `c`.`id`', [])
Select(tables=teacher.join(teach, teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id), where=(class_.id == '123123'), fields=[teacher.builtin_all]).sql
# ('SELECT `teacher`.* FROM `teacher` INNER JOIN `teach` AS `ss` ON `ss`.`teacher_id` = `teacher
`.`id` INNER JOIN `class` AS `c` ON `c`.`id` = `ss`.`class_id` WHERE `c`.`id` = %s', ['123123'
])
Select(tables=teacher.join(teach, teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id)).where(class_.id == '123123').select(teacher.builtin_all).sql
# ('SELECT `teacher`.* FROM `teacher` INNER JOIN `teach` AS `ss` ON `ss`.`teacher_id` = `teacher
`.`id` INNER JOIN `class` AS `c` ON `c`.`id` = `ss`.`class_id` WHERE `c`.`id` = %s', ['123123'
])



Insert(student, student.id, 1, student.name, "学生a", student.class_id, "21321").on_duplicate_key_fields(student.name, "学生a").sql
# ('INSERT INTO `student`(id, name, class_id) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE `name`=%s', [1, '学生a', '21321', '学生a'])
sub = Select(student).where(student.name == 'test').select(
    student.id, student.name, student.class_id, student.age).as_table("old_student")
InsertFromSelect(ss, [ss.id, ss.name, ss.class_id, ss.age], sub).sql
# ('INSERT INTO `student_snapshot`(`snapshot`.`id`, `snapshot`.`name`, `snapshot`.`class_id`, `snapshot`.`age`) (SELECT `s`.`id`, `s`.`name`, `s`.`class_id`, `s`.`age` FROM `student` AS `s` WHERE `s`.`name` = %s) AS `old_student`', ['test'])


Update(student, student.name, "学生").where(student.id == 1).sql
# ('UPDATE `student` SET `s`.`name`=%s WHERE `s`.`id` = %s', ['学生', 1])


Delete(table=student).where(student.id == 1).sql
# ('DELETE FROM `student` AS `s` WHERE `s`.`id` = %s', [1])
Delete(table=teacher).where(teacher.id.in_(Select(tables=teach.join(teacher, teach.teacher_id == teacher.id)).select(teacher.id).where((teach.class_id == 2) & (teacher.deleted == 0)))).sql
# ('DELETE FROM `teacher` WHERE `teacher`.`id` IN (SELECT `teacher`.`id` FROM `teach` AS `ss` INNER JOIN `teacher` ON `ss`.`teacher_id` = `teacher`.`id` WHERE `ss`.`class_id` = %s AND `teacher`.`deleted` = %s)', [2, 0])

```
