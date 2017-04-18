# sql()-builder
A tool to build sql() statement, avoiding to write SQLs directly. 


## Install
```sh
pip install sql()-builder
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
import sql()_builder


student = Table("student").as_("s")
ss = Table("student_snapshot").as_("snapshot")
class_ = Table("class").as_("c")
teacher = Table("teacher")
teach = Table("teach").as_("ss")

student.select(student.builtin_all, student.age.max_()).sql()
# ('SELECT `s`.*, MAX(`s`.`age`) FROM `student` AS `s`', [])

student.select(student.builtin_all, student.age.max_("max_age"))[0:4].sql()
# ('SELECT `s`.*, MAX(`s`.`age`) AS `max_age` FROM `student` AS `s` LIMIT 0, 4', [])

student.join(class_, student.class_id == class_.id).select().sql()
# ('SELECT * FROM `student` AS `s` INNER JOIN `class` AS `c` ON `s`.`class_id` = `c`.`id`', [])

teacher.join(teach, teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id).select(teacher.builtin_all).where(class_.id == '12321').sql()
# ('SELECT `teacher`.* FROM `teacher` INNER JOIN `teach` AS `ss` ON `ss`.`teacher_id` = `teacher`.`id` INNER JOIN `class` AS `c` ON `c`.`id` = `ss`.`class_id` WHERE `c`.`id` = %s', ['123123'])

teacher.join(teach, teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id).select(teacher.builtin_all).where(class_.id == '123123').sql()
# ('SELECT `teacher`.* FROM `teacher` INNER JOIN `teach` AS `ss` ON `ss`.`teacher_id` = `teacher`.`id` INNER JOIN `class` AS `c` ON `c`.`id` = `ss`.`class_id` WHERE `c`.`id` = %s', ['123123'])


student.insert(student.id, 1, student.name, "学生a", student.class_id, "21321").on_duplicate_key_fields(student.name, "学生a").sql()
# ('INSERT INTO `student`(id, name, class_id) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE `name`=%s', [1, '学生a', '21321', '学生a'])

sub = student.select(student.id, student.name, student.class_id, student.age).where(student.name == 'test').as_table("old_student")

InsertFromSelect(ss, [ss.id, ss.name, ss.class_id, ss.age], sub).sql()
# ('INSERT INTO `student_snapshot`(`snapshot`.`id`, `snapshot`.`name`, `snapshot`.`class_id`, `snapshot`.`age`) (SELECT `s`.`id`, `s`.`name`, `s`.`class_id`, `s`.`age` FROM `student` AS `s` WHERE `s`.`name` = %s) AS `old_student`', ['test'])


student.update(student.name, "学生").where(student.id == 1).sql()
# ('UPDATE `student` SET `s`.`name`=%s WHERE `s`.`id` = %s', ['学生', 1])


student.delete().where((student.name == 'allen')&(student.id != '1231')).sql()
# ('DELETE FROM `student` AS `s` WHERE `s`.`name` = %s AND `s`.`id` != %s',['allen', '1231'])

teacher.delete().where(teacher.id.in_(Select(tables=teach.join(teacher, teach.teacher_id == teacher.id)).select(teacher.id).where((teach.class_id == 2) & (teacher.deleted == 0)))).sql()
# ('DELETE FROM `teacher` WHERE `teacher`.`id` IN (SELECT `teacher`.`id` FROM `teach` AS `ss` INNER JOIN `teacher` ON `ss`.`teacher_id` = `teacher`.`id` WHERE `ss`.`class_id` = %s AND `teacher`.`deleted` = %s)', [2, 0])

```
