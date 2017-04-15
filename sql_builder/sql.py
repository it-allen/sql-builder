# coding: utf-8
# Author: Allen Zou
# 2017/4/6 下午2:38
import collections
import weakref


class _Column(object):
    @property
    def field_view(self):
        raise NotImplemented

    @property
    def where_view(self):
        raise NotImplemented

    @property
    def insert_view(self):
        raise NotImplemented

    @property
    def update_view(self):
        raise NotImplemented

    @property
    def raw_view(self):
        raise NotImplemented


class Column(_Column):
    def __init__(self, name=None, alias=None, table=None):
        self.name = name
        self.alias = alias
        self._table = None
        self.table = table

    @property
    def table(self):
        if self._table is None:
            return None
        return self._table()

    @table.setter
    def table(self, t):
        if t is None:
            self._table = None
        else:
            assert isinstance(t, Table)
            self._table = weakref.ref(t)

    @property
    def raw_view(self):
        if not self.name:
            raise ValueError()
        s = "`{}`".format(self.name)
        if self.table:
            s = "{}.{}".format(self.table.where_view, s)
        return s

    @property
    def field_view(self):
        if not self.name:
            if self.table:
                return "{}.*".format(self.table.field_view)
            return "*"
        if self.alias:
            return "{} AS `{}`".format(self.raw_view, self.alias)
        return self.raw_view

    @property
    def where_view(self):
        return self.raw_view

    @property
    def insert_view(self):
        if not self.name:
            raise ValueError()
        return "`{}`".format(self.name)

    @property
    def update_view(self):
        return self.raw_view

    def as_(self, alias):
        self.alias = alias

    def __gt__(self, other):
        return Condition(self, Condition.OP_GT, other)

    def __ge__(self, other):
        return Condition(self, Condition.OP_GE, other)

    def __lt__(self, other):
        return Condition(self, Condition.OP_LT, other)

    def __le__(self, other):
        return Condition(self, Condition.OP_LE, other)

    def __eq__(self, other):
        return Condition(self, Condition.OP_EQ, other)

    def __ne__(self, other):
        return Condition(self, Condition.OP_NE, other)

    def in_(self, value):
        return Condition(self, Condition.OP_IN, value)

    def nin(self, value):
        return Condition(self, Condition.OP_NIN, value)

    def like(self, value):
        return Condition(self, Condition.OP_LIKE, value)

    def unlike(self, value):
        return Condition(self, Condition.OP_NOT_LIKE, value)

    def startswith(self, value):
        return Condition(self, Condition.OP_PREFIX, value)

    def endswith(self, value):
        return Condition(self, Condition.OP_SUFFIX, value)


class Max(_Column):
    def __init__(self, column, alias=None):
        assert isinstance(column, Column)
        self.column = column
        self.alias = alias

    @property
    def sql(self):
        s = "MAX({})".format(self.column.raw)
        if self.alias:
            s = "{} AS `{}`".format(s, self.alias)
        return s

    @property
    def raw_view(self):
        return "MAX({})".format(self.column.raw_view)

    @property
    def field_view(self):
        if self.alias:
            return "{} AS `{}`".format(self.raw_view, self.alias)
        return self.raw_view


class _Table(object):
    @property
    def raw_view(self):
        raise NotImplemented

    @property
    def field_view(self):
        raise NotImplemented

    @property
    def from_view(self):
        raise NotImplemented

    @property
    def where_view(self):
        raise NotImplemented


class Table(_Table):
    def __init__(self, name, db=None, alias=None):
        self._b_name = name
        self._b_db = db
        self._b_alias = alias
        self._b_explicit_columns = {}

    def as_(self, alias):
        self._b_alias = alias
        return self

    def __getattr__(self, column):
        if column not in self._b_explicit_columns:
            self._b_explicit_columns[column] = Column(name=column, table=self)
        return self._b_explicit_columns[column]

    def __getitem__(self, item):
        return getattr(self, item)

    # @property
    # def all(self):
    #     return Column(table=self)

    @property
    def raw_view(self):
        s = "`{}`".format(self._b_name)
        if self._b_db:
            s = "`{}`.{}".format(self._b_db, s)
        return s

    @property
    def field_view(self):
        if self._b_alias:
            return "`{}`".format(self._b_alias)
        return self.raw_view

    @property
    def from_view(self):
        if self._b_alias:
            return "{} AS `{}`".format(self.raw_view, self._b_alias)
        return self.raw_view

    @property
    def where_view(self):
        return self.field_view

    def left_join(self, other, condition):
        return TableJoin(self).left_join(other, condition)

    def right_join(self, other, condition):
        return TableJoin(self).right_join(other, condition)

    def inner_join(self, other, condition):
        return TableJoin(self).inner_join(other, condition)

    def outer_join(self, other, condition):
        return TableJoin(self).outer_join(other, condition)

    def join(self, other, condition):
        return TableJoin(self).join(other, condition)


class TableJoin(_Table):
    LEFT_JOIN = "LEFT JOIN"
    INNER_JOIN = "INNER JOIN"
    RIGHT_JOIN = "RIGHT JOIN"
    OUTER_JOIN = "OUTER JOIN"
    JOIN = INNER_JOIN
    JoinTuple = collections.namedtuple("JoinTuple", ["method", "table", "condition"])

    def __init__(self, base_table):
        assert isinstance(base_table, Table)
        self.base = base_table
        self.join_items = []

    def join(self, table, condition, method=JOIN):
        assert method in [TableJoin.LEFT_JOIN, TableJoin.INNER_JOIN,
                          TableJoin.RIGHT_JOIN, TableJoin.OUTER_JOIN]
        assert isinstance(condition, (ConditionUnion, Condition))
        assert isinstance(table, Table)
        self.join_items.append(TableJoin.JoinTuple(method, table, condition))
        return self

    def left_join(self, table, condition):
        return self.join(table, condition, TableJoin.LEFT_JOIN)

    def right_join(self, table, condition):
        return self.join(table, condition, TableJoin.RIGHT_JOIN)

    def inner_join(self, table, condition):
        return self.join(table, condition, TableJoin.INNER_JOIN)

    def outer_join(self, table, condition):
        return self.join(table, condition, TableJoin.OUTER_JOIN)

    @property
    def from_view(self):
        pieces = [self.base.from_view]
        for each in self.join_items:
            pieces.append("{} {} ON {}".format(each.method, each.table.from_view, each.condition.sql[0]))
        return " ".join(pieces)


class _Where(object):
    def __and__(self, other):
        pass

    def __or__(self, other):
        pass

    def __invert__(self):
        pass

    @property
    def sql(self):
        return


class Condition(_Where):
    OP_EQ = "="
    OP_NE = "!="
    OP_GE = ">="
    OP_GT = ">"
    OP_LE = "<="
    OP_LT = "<"
    OP_IN = "$in"
    OP_NIN = "$nin"
    OP_LIKE = "$like"
    OP_NOT_LIKE = "$unlike"
    OP_PREFIX = "$prefix"
    OP_NOT_PREFIX = "$not_prefix"
    OP_SUFFIX = "$suffix"
    OP_NOT_SUFFIX = "$not_suffix"

    def __init__(self, column, op, value):
        assert isinstance(column, Column)
        self.column = column
        self.op = op
        if op in (Condition.OP_IN, Condition.OP_NIN):
            assert isinstance(value, (list, tuple)) and len(value) > 0 or isinstance(value, Select)
        if op in (Condition.OP_LIKE, Condition.OP_NOT_LIKE, Condition.OP_PREFIX,
                  Condition.OP_SUFFIX):
            assert isinstance(value, str)
            assert len(value) > 0
        self.value = value

    def _op_2_sql(self, op):
        if op == Condition.OP_EQ: return "="
        if op == Condition.OP_NE: return "!="
        if op == Condition.OP_GE: return ">="
        if op == Condition.OP_GT: return ">"
        if op == Condition.OP_LE: return "<="
        if op == Condition.OP_LT: return "<"
        if op == Condition.OP_IN: return "IN"
        if op == Condition.OP_NIN: return "NOT IN"
        if op == Condition.OP_LIKE: return "LIKE"
        if op == Condition.OP_NOT_LIKE: return "NOT LIKE"
        if op == Condition.OP_PREFIX: return "LIKE"
        if op == Condition.OP_NOT_PREFIX: return "NOT LIKE"
        if op == Condition.OP_SUFFIX: return "LIKE"
        if op == Condition.OP_NOT_SUFFIX: return "NOT LIKE"

    def __invert__(self):
        if self.op == Condition.OP_EQ:
            self.op = Condition.OP_NE
        elif self.op == Condition.OP_NE:
            self.op = Condition.OP_EQ
        elif self.op == Condition.OP_GE:
            self.op = Condition.OP_LT
        elif self.op == Condition.OP_GT:
            self.op = Condition.OP_LE
        elif self.op == Condition.OP_LE:
            self.op = Condition.OP_GT
        elif self.op == Condition.OP_LT:
            self.op = Condition.OP_GE
        elif self.op == Condition.OP_IN:
            self.op = Condition.OP_NIN
        elif self.op == Condition.OP_NIN:
            self.op = Condition.OP_IN
        elif self.op == Condition.OP_LIKE:
            self.op = Condition.OP_NOT_LIKE
        elif self.op == Condition.OP_NOT_LIKE:
            self.op = Condition.OP_LIKE
        elif self.op == Condition.OP_PREFIX:
            self.op = Condition.OP_NOT_PREFIX
        elif self.op == Condition.OP_NOT_PREFIX:
            self.op = Condition.OP_PREFIX
        elif self.op == Condition.OP_SUFFIX:
            self.op = Condition.OP_NOT_SUFFIX
        elif self.op == Condition.OP_NOT_SUFFIX:
            self.op = Condition.OP_SUFFIX
        else:
            raise ValueError()

    @property
    def sql(self):
        sql_pieces = [self.column.where_view, self._op_2_sql(self.op)]
        args = []
        sub_sql, sub_args = self.value.sql() if isinstance(self.value, Select) else ("", [])
        if self.op in [Condition.OP_IN, Condition.OP_NIN]:
            if isinstance(self.value, Select):
                sql_pieces.append("({})".format(sub_sql))
                args.extend(sub_args)
            else:
                sql_pieces.append("({})".format(",".join("%s" for _ in self.value)))
                args.extend(self.value)
        elif self.op in [Condition.OP_LIKE, Condition.OP_NOT_LIKE]:
            sql_pieces.append("%%{}%%".format(self.value))
        elif self.op in [Condition.OP_PREFIX, Condition.OP_NOT_PREFIX]:
            sql_pieces.append("{}%%".format(self.value))
        elif self.op in [Condition.OP_SUFFIX, Condition.OP_NOT_SUFFIX]:
            sql_pieces.append("%%{}".format(self.value))
        else:
            if isinstance(self.value, Column):
                sql_pieces.append(self.value.where_view)
            elif isinstance(self.value, Select):
                sql_pieces.append("({})".format(sub_sql))
                args.extend(sub_args)
            else:
                sql_pieces.append("%s")
                args.append(self.value)
        return " ".join(sql_pieces), args

    def __and__(self, other):
        assert isinstance(other, _Where)
        return ConditionUnion(self, other, ConditionUnion.OP_AND)

    def __or__(self, other):
        assert isinstance(other, _Where)
        return ConditionUnion(self, other, ConditionUnion.OP_OR)


class ConditionUnion(_Where):
    OP_AND = "$and"
    OP_OR = "$or"

    def __init__(self, left_conf, right_cond, op):
        assert isinstance(left_conf, _Where)
        assert isinstance(right_cond, _Where)
        self.left = left_conf
        self.right = right_cond
        self.op = op

    def __and__(self, other):
        return ConditionUnion(self, other, ConditionUnion.OP_AND)

    def __or__(self, other):
        return ConditionUnion(self, other, ConditionUnion.OP_OR)

    def __invert__(self):
        if self.op == ConditionUnion.OP_AND:
            return ConditionUnion(~self.left, ~self.right, ConditionUnion.OP_OR)
        elif self.op == ConditionUnion.OP_OR:
            return ConditionUnion(~self.left, ~self.right, ConditionUnion.OP_AND)
        else:
            raise ValueError()

    @property
    def sql(self):
        args = []
        left_sql, left_args = self.left.sql
        right_sql, right_args = self.right.sql
        args.extend(left_args)
        args.extend(right_args)
        left_sql = ("{}" if isinstance(self.left, Condition) else "({})").format(left_sql)
        right_sql = ("{}" if isinstance(self.right, Condition) else "({})").format(right_sql)
        if self.op == ConditionUnion.OP_AND:
            tpl = "{} AND {}"
        else:
            tpl = "{} OR {}"
        return tpl.format(left_sql, right_sql), args

    def __str__(self):
        return "{}: {} {}".format(super(ConditionUnion, self).__str__(), *self.sql)


class Sort(object):
    ASC = "ASC"
    DESC = "DESC"

    def __init__(self, col, order=ASC):
        assert isinstance(col, Column)
        assert order in [Sort.ASC, Sort.DESC]
        self._tuples = [[col, order]]

    def asc(self, col):
        assert isinstance(col, Column)
        self._tuples.append([col, Sort.ASC])

    def desc(self, col):
        assert isinstance(col, Column)
        self._tuples.append([col, Sort.DESC])

    @property
    def sql(self):
        return ", ".join("{} {}".format(col.raw_view, method) for col, method in self._tuples)


class GroupBy(object):
    def __init__(self, *cols):
        assert cols
        for col in cols:
            assert isinstance(col, Column)
        self._cols = cols

    @property
    def sql(self):
        return ", ".join(col.raw_view for col in self._cols)


class _Query(object):
    UpdatePair = collections.namedtuple("UpdatePair", ["field", "value"])

    def __init__(self, tables):
        assert isinstance(tables, _Table)
        self._tables = tables


class Insert(_Query):
    def __init__(self, table, *pairs):
        assert isinstance(table, Table)
        super(Insert, self).__init__(tables=table)
        assert pairs and len(pairs) % 2 == 0
        self._pairs = []
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is table
            self._pairs.append(_Query.UpdatePair(key, val))
        self._on_duplicate_update_fields = []

    def on_duplicate_key_fields(self, *pairs):
        assert pairs and len(pairs) % 2 == 0
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            self._on_duplicate_update_fields.append(_Query.UpdatePair(key, val))
        return self

    def sql(self):
        sql_pieces = ["INSERT INTO {table}({fields}) VALUES({placeholders})".format(table=self._tables.raw_view,
                                                                                    fields=", ".join(
                                                                                        pair.field.name for pair
                                                                                        in self._pairs),
                                                                                    placeholders=", ".join(
                                                                                        ["%s"] * len(self._pairs)))]
        args = [pair.value for pair in self._pairs]
        if self._on_duplicate_update_fields:
            sql_pieces.append("ON DUPLICATE KEY UPDATE {}".format(
                ", ".join("{}=%s".format(pair.field.insert_view) for pair in self._on_duplicate_update_fields)))
            args.extend([pair.value for pair in self._on_duplicate_update_fields])
        return " ".join(sql_pieces), args


class Update(_Query):
    def __init__(self, table, *pairs):
        assert isinstance(table, Table)
        super(Update, self).__init__(tables=table)
        assert pairs and len(pairs) % 2 == 0
        self._pairs = []
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is table
            self._pairs.append(_Query.UpdatePair(key, val))

    def where(self, cond):
        assert cond is None or isinstance(cond, _Where)
        self._where = cond
        return self

    def sql(self):
        sql_pieces = ["UPDATE {table} SET {fields}".format(table=self._tables.raw_view,
                                                           fields=", ".join(
                                                               "{}=%s".format(pair.field.update_view) for pair in
                                                               self._pairs))]
        args = [pair.value for pair in self._pairs]
        if self._where:
            where_clause, where_args = self._where.sql
            sql_pieces.append("WHERE {}".format(where_clause))
            args.extend(where_args)
        return " ".join(sql_pieces), args


class Select(_Query):
    def __init__(self, tables, fields=None, where=None, sort=None, group=None, offset=0, count=0):
        super(Select, self).__init__(tables)
        assert fields is None or (isinstance(fields, (list, tuple)))
        if fields:
            for field in fields:
                assert isinstance(field, _Column)
        assert where is None or isinstance(where, _Where)
        assert sort is None or isinstance(sort, Sort)
        assert group is None or isinstance(group, GroupBy)
        assert offset >= 0
        assert count >= 0
        self._fields = fields
        self._where = where
        self._sort = sort
        self._group = group
        self._offset = offset
        self._count = count

    def sql(self):
        sql_pieces = []
        args = []
        fields = self._fields and ", ".join(
            field.field_view for field in self._fields) or "*"
        sql_pieces.append("SELECT {fields} FROM {tables}".format(fields=fields, tables=self._tables.from_view))
        if self._where:
            where_clause, where_args = self._where.sql
            sql_pieces.append("WHERE {where}".format(where=where_clause))
            args.extend(where_args)
        if self._sort:
            sql_pieces.append("ORDER BY {}".format(self._sort.sql))
        if self._group:
            sql_pieces.append("GROUP BY {}".format(self._group.sql))
        if self._count > 0:
            sql_pieces.append("LIMIT {:d}, {:d}".format(self._offset, self._count))
        return " ".join(sql_pieces), args


class Delete(_Query):
    def __init__(self, table, where=None):
        assert isinstance(table, Table)
        super(Delete, self).__init__(tables=table)
        self.where(where)

    def where(self, cond):
        assert cond is None or isinstance(cond, _Where)
        self._where = cond
        return self

    def sql(self):
        sql_pieces = ["DELETE FROM {table}".format(table=self._tables.from_view)]
        args = []
        if self._where:
            where_clause, where_args = self._where.sql
            sql_pieces.append("WHERE {}".format(where_clause))
            args.extend(where_args)
        return " ".join(sql_pieces), args


if __name__ == "__main__":
    # test here>>>
    """
    class: id, name
    student: id, name, class_id(class:id), age
    teacher: id, name
    teach: teacher_id(teacher:id), class_id(class:id)
    """
    student = Table("student").as_("s")
    class_ = Table("class").as_("c")
    teacher = Table("teacher")
    teach = Table("teach").as_("ss")
    print(Select(tables=student, fields=[student.all, Max(student.age, "max_age")]).sql())
    print(Select(tables=student.join(class_, student.class_id == class_.id)).sql())
    print(Select(tables=teacher.join(teach,
                                     teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id),
                 where=(class_.id == '123123'), fields=[teacher.all]).sql())
    print("=" * 20)
    print(Insert(student, student.id, 1, student.name, "学生a", student.class_id, "21321").on_duplicate_key_fields(
        student.name, "学生a").sql())

    print(Update(student, student.name, "学生").where(student.id == 1).sql())
    print(Delete(table=student, where=student.id == 1).sql())
    print(Delete(table=teacher, where=teacher.id.in_(
        Select(tables=teach.join(teacher, teach.teacher_id == teacher.id), fields=[teacher.id],
               where=teach.class_id == 2)) & (teacher.deleted == 0)).sql())
