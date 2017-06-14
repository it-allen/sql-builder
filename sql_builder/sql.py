# coding: utf-8
# Author: Allen Zou
# 2017/4/6 下午2:38
import collections
import sys
import weakref

if sys.version_info >= (3, 0):
    basestring = str


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


class RawSQLField(_Column):
    def __init__(self, piece):
        self.piece = piece

    @property
    def field_view(self):
        return self.piece


class Column(_Column):
    def __init__(self, table, name=None, alias=None):
        self.name = name
        self.alias = alias
        self._table = None
        self.table = table

    def __hash__(self):
        return hash(self.raw_view)

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
            assert isinstance(t, _Table)
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
        return self

    def __gt__(self, other):
        return Condition(self, Condition.OP_GT, other)

    def gt(self, other):
        return self > other

    def __ge__(self, other):
        return Condition(self, Condition.OP_GE, other)

    def ge(self, other):
        return self >= other

    def __lt__(self, other):
        return Condition(self, Condition.OP_LT, other)

    def lt(self, other):
        return self < other

    def __le__(self, other):
        return Condition(self, Condition.OP_LE, other)

    def le(self, other):
        return self <= other

    def __eq__(self, other):
        return Condition(self, Condition.OP_EQ, other)

    def eq(self, other):
        return self == other

    def __ne__(self, other):
        return Condition(self, Condition.OP_NE, other)

    def ne(self, other):
        return self != other

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

    def max_(self, alias=None):
        return Max(self, alias)

    def min_(self, alias=None):
        return Min(self, alias)

    def count(self, alias=None):
        return Count(self, alias)

    def update(self, value):
        return ColumnUpdating(self, value)

    def inc(self, step=1):
        return ColumnUpdating(self, step, ColumnUpdating.OP_INC)

    def dec(self, step=1):
        return ColumnUpdating(self, step, ColumnUpdating.OP_DEC)


class ColumnUpdating(object):
    OP_ASSIGN = "="
    OP_INC = "$inc"
    OP_DEC = "$dec"
    ops = [
        OP_ASSIGN,
        OP_INC,
        OP_DEC
    ]

    def __init__(self, column, value, op=OP_ASSIGN):
        assert isinstance(column, Column)
        assert op in self.ops
        self.column = column
        self.op = op
        self.value = value

    def sql(self, placeholder="%s"):
        if self.op == self.OP_ASSIGN:
            tpl = "{col} = {placeholder}"
        elif self.op == self.OP_INC:
            tpl = "{col} = {col} + {placeholder}"
        else:
            tpl = "{col} = {col} - {placeholder}"
        col = "`{}`".format(self.column.name)
        if isinstance(self.value, Column):
            return tpl.format(col=col, placeholder=self.value.raw_view), []
        return tpl.format(col=col, placeholder=placeholder), [self.value]


class Max(_Column):
    def __init__(self, column, alias=None):
        assert isinstance(column, Column)
        self.column = column
        self.alias = alias

    def __hash__(self):
        return hash(self.raw_view)

    @property
    def sql(self):
        s = "MAX({})".format(self.column.raw_view)
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


class Min(_Column):
    def __init__(self, column, alias=None):
        assert isinstance(column, Column)
        self.column = column
        self.alias = alias

    def __hash__(self):
        return hash(self.raw_view)

    @property
    def raw_view(self):
        return "MIN({})".format(self.column.raw_view)

    @property
    def field_view(self):
        if self.alias:
            return "{} AS `{}`".format(self.raw_view, self.alias)
        return self.raw_view


class Count(_Column):
    def __init__(self, column, alias=None):
        assert isinstance(column, Column)
        self.column = column
        self.alias = alias

    def __hash__(self):
        return hash(self.raw_view)

    @property
    def raw_view(self):
        return "COUNT({})".format(self.column.raw_view)

    @property
    def field_view(self):
        if self.alias:
            return "{} AS `{}`".format(self.raw_view, self.alias)
        return self.raw_view


class _Table(object):
    def __getattr__(self, column):
        return self[column]

    def __getitem__(self, column):
        return Column(name=column, table=self)

    @property
    def builtin_all(self):
        return Column(table=self)

    @property
    def raw_view(self):
        raise NotImplemented()

    @property
    def field_view(self):
        raise NotImplemented()

    def from_view(self, placeholder="%s"):
        raise NotImplemented()

    @property
    def where_view(self):
        raise NotImplemented()

    def select(self, *fields):
        return Select(self, fields=fields)

    def update(self, *pairs, **pairs_kwargs):
        return Update(self, *pairs, **pairs_kwargs)

    def insert(self, *pairs, **pairs_kwargs):
        return Insert(self, *pairs, **pairs_kwargs)

    def delete(self, where=None):
        return Delete(self, where)


class _SubQueryTable(_Table):
    def __init__(self, alias, query):
        assert isinstance(query, Select)
        self._alias = alias
        self._query = query

    def from_view(self, placeholder="%s"):
        sub_query_sql, sub_query_args = self._query.sql(placeholder)
        return "({}) AS `{}`".format(sub_query_sql, self._alias), sub_query_args

    @property
    def field_view(self):
        return "`{}`".format(self._alias)

    @property
    def where_view(self):
        return "`{}`".format(self._alias)


class Table(_Table):
    def __init__(self, name, db=None, alias=None):
        self._b_name = name
        self._b_db = db
        self._b_alias = alias

    def __hash__(self):
        return hash(self.raw_view)

    def __contains__(self, item):
        return hash(item) == hash(item)

    def as_(self, alias):
        self._b_alias = alias
        return self

    def copy(self):
        return Table(name=self._b_name, db=self._b_db, alias=self._b_alias)

    @property
    def raw_view(self):
        s = "`{}`".format(self._b_name)
        if self._b_db:
            s = "`{}`.{}".format(self._b_db, s)
        return s

    def insert_from_select(self, fields, select):
        return InsertFromSelect(self, fields, select)

    @property
    def field_view(self):
        if self._b_alias:
            return "`{}`".format(self._b_alias)
        return self.raw_view

    def from_view(self, placeholder="%s"):
        if self._b_alias:
            return "{} AS `{}`".format(self.raw_view, self._b_alias), []
        return self.raw_view, []

    @property
    def where_view(self):
        return self.field_view

    def left_join(self, other, condition):
        return TableJoin(self).left_join(other, condition)

    def right_join(self, other, condition):
        return TableJoin(self).right_join(other, condition)

    def inner_join(self, other, condition):
        return TableJoin(self).inner_join(other, condition)

    def full_join(self, other, condition):
        return TableJoin(self).full_join(other, condition)

    def join(self, other, condition):
        return TableJoin(self).join(other, condition)

    def select(self, *fields):
        return super(Table, self).select(
            *[getattr(self, field) if isinstance(field, basestring) else field for field in fields])


class TableJoin(_Table):
    LEFT_JOIN = "LEFT JOIN"
    INNER_JOIN = "INNER JOIN"
    RIGHT_JOIN = "RIGHT JOIN"
    FULL_JOIN = "FULL JOIN"
    JOIN = INNER_JOIN
    JoinTuple = collections.namedtuple("JoinTuple", ["method", "table", "condition"])

    def __init__(self, base_table):
        assert isinstance(base_table, _Table)
        self.base = base_table
        self.join_items = []

    def __contains__(self, item):
        tables = {t.table for t in self.join_items}
        tables.add(self.base)
        return item in tables

    def join(self, table, condition, method=JOIN):
        assert method in [TableJoin.LEFT_JOIN, TableJoin.INNER_JOIN,
                          TableJoin.RIGHT_JOIN, TableJoin.FULL_JOIN]
        assert isinstance(condition, (ConditionUnion, Condition))
        assert isinstance(table, _Table)
        self.join_items.append(TableJoin.JoinTuple(method, table, condition))
        return self

    def left_join(self, table, condition):
        return self.join(table, condition, TableJoin.LEFT_JOIN)

    def right_join(self, table, condition):
        return self.join(table, condition, TableJoin.RIGHT_JOIN)

    def inner_join(self, table, condition):
        return self.join(table, condition, TableJoin.INNER_JOIN)

    def full_join(self, table, condition):
        return self.join(table, condition, TableJoin.FULL_JOIN)

    def from_view(self, placeholder="%s"):
        args = []
        base_sql, base_args = self.base.from_view(placeholder)
        pieces = [base_sql]
        args.extend(base_args)
        for each in self.join_items:
            tbl_sql, tbl_args = each.table.from_view(placeholder)
            args.extend(tbl_args)
            cond_sql, cond_args = each.condition.sql(placeholder)
            args.extend(cond_args)
            pieces.append("{} {} ON {}".format(each.method, tbl_sql, cond_sql))
        return " ".join(pieces), args


class _Where(object):
    def __and__(self, other):
        pass

    def __or__(self, other):
        pass

    def __invert__(self):
        pass

    def sql(self, placeholder="%s"):
        return

    def is_empty(self):
        return False


class EmptyCond(_Where):
    def is_empty(self):
        return True

    def __and__(self, other):
        return other

    def __or__(self, other):
        return other

    def __invert__(self):
        return self


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
            assert isinstance(value, basestring)
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

    def sql(self, placeholder="%s"):
        key = self.column.where_view
        op = self._op_2_sql(self.op)
        # sql_pieces = [self.column.where_view, self._op_2_sql(self.op)]
        args = []
        sub_sql, sub_args = self.value.sql(placeholder) if isinstance(self.value, Select) else ("", [])
        if self.op in [Condition.OP_IN, Condition.OP_NIN]:
            if isinstance(self.value, Select):
                value = "({})".format(sub_sql)
                args.extend(sub_args)
            else:
                value = "({})".format(",".join(placeholder for _ in self.value))
                args.extend(self.value)
        elif self.op in [Condition.OP_LIKE, Condition.OP_NOT_LIKE]:
            value = "'%%{}%%'".format(self.value)
        elif self.op in [Condition.OP_PREFIX, Condition.OP_NOT_PREFIX]:
            value = "'{}%%'".format(self.value)
        elif self.op in [Condition.OP_SUFFIX, Condition.OP_NOT_SUFFIX]:
            value = "'%%{}'".format(self.value)
        elif self.op in [Condition.OP_EQ, Condition.OP_NE]:
            if self.value is None:
                op = "IS" if self.op == Condition.OP_EQ else "IS NOT"
                value = "NULL"
            elif isinstance(self.value, Column):
                value = self.value.where_view
            elif isinstance(self.value, Select):
                value = "({})".format(sub_sql)
                args.extend(sub_args)
            else:
                value = placeholder
                args.append(self.value)
        else:
            if isinstance(self.value, Column):
                value = self.value.where_view
            elif isinstance(self.value, Select):
                value = "({})".format(sub_sql)
                args.extend(sub_args)
            else:
                value = placeholder
                args.append(self.value)
        return " ".join([key, op, value]), args

    def __and__(self, other):
        assert isinstance(other, _Where)
        if isinstance(other, EmptyCond):
            return self
        return ConditionUnion(self, other, ConditionUnion.OP_AND)

    def __or__(self, other):
        assert isinstance(other, _Where)
        if isinstance(other, EmptyCond):
            return self
        return ConditionUnion(self, other, ConditionUnion.OP_OR)


class ConditionUnion(_Where):
    OP_AND = "$and"
    OP_OR = "$or"

    def __init__(self, left_conf, right_cond, op):
        assert isinstance(left_conf, _Where) and not isinstance(left_conf, EmptyCond)
        assert isinstance(right_cond, _Where) and not isinstance(right_cond, EmptyCond)
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

    def sql(self, placeholder="%s"):
        args = []
        left_sql, left_args = self.left.sql(placeholder)
        right_sql, right_args = self.right.sql(placeholder)
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
        return "{}: {} {}".format(super(ConditionUnion, self).__str__(), *self.sql())


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
    def __init__(self, table, *pairs, **pairs_kwargs):
        assert isinstance(table, Table)
        super(Insert, self).__init__(tables=table)
        assert len(pairs) % 2 == 0
        self._pairs = []
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is table
            self._pairs.append(_Query.UpdatePair(key, val))
        for key, val in pairs_kwargs.items():
            self._pairs.append(_Query.UpdatePair(getattr(table, key), val))
        self._on_duplicate_update_fields = []

    def add_fields(self, *pairs, **pairs_kwargs):
        assert len(pairs) % 2 == 0
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is self._tables
            self._pairs.append(_Query.UpdatePair(key, val))
        for key, val in pairs_kwargs.items():
            self._pairs.append(_Query.UpdatePair(getattr(self._tables, key), val))
        return self

    def on_duplicate_key_fields(self, *pairs, **pairs_kwargs):
        assert len(pairs) % 2 == 0
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            self._on_duplicate_update_fields.append(ColumnUpdating(key, val))
        for key, val in pairs_kwargs.items():
            self._on_duplicate_update_fields.append(ColumnUpdating(getattr(self._tables, key), val))
        return self

    def on_duplicate_key_update(self, *updating):
        for each in updating:
            assert isinstance(each, ColumnUpdating)
            self._on_duplicate_update_fields.append(each)
        return self

    def sql(self, placeholder="%s"):
        sql_pieces = ["INSERT INTO {table}({fields}) VALUES({placeholders})".format(table=self._tables.raw_view,
                                                                                    fields=", ".join(
                                                                                        pair.field.insert_view for pair
                                                                                        in self._pairs),
                                                                                    placeholders=", ".join(
                                                                                        [placeholder] * len(
                                                                                            self._pairs)))]
        args = [pair.value for pair in self._pairs]
        if self._on_duplicate_update_fields:
            ts = []
            update_args = []
            for each in self._on_duplicate_update_fields:
                s, a = each.sql(placeholder)
                ts.append(s)
                update_args.extend(a)
            sql_pieces.append("ON DUPLICATE KEY UPDATE {}".format(
                ", ".join(ts)
            ))
            args.extend(update_args)
            # sql_pieces.append("ON DUPLICATE KEY UPDATE {}".format(
            #     ", ".join("{}={}".format(pair.field.insert_view, placeholder) for pair in self._on_duplicate_update_fields)))
            # args.extend([pair.value for pair in self._on_duplicate_update_fields])
        return " ".join(sql_pieces), args


class InsertFromSelect(_Query):
    def __init__(self, table, fields, sub_query):
        assert isinstance(table, Table)
        super(InsertFromSelect, self).__init__(table)
        assert fields is None or isinstance(fields, (list, tuple))
        if fields:
            for field in fields:
                assert (isinstance(field, Column))
        self._fields = fields
        assert isinstance(sub_query, (Select, _SubQueryTable))
        self._sub_query = sub_query
        self._on_duplicate_update_fields = []

    def on_duplicate_key_fields(self, *pairs):
        if not isinstance(self._sub_query, _SubQueryTable):
            raise TypeError("The sub-query must be used as a table")
        assert pairs and len(pairs) % 2 == 0
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is self._tables
            assert isinstance(val, Column)
            assert val.table is self._sub_query
            self._on_duplicate_update_fields.append(ColumnUpdating(key, val))
        return self

    def on_duplicate_key_update(self, *updating, **kwargs):
        for each in updating:
            assert isinstance(each, ColumnUpdating)
            self._on_duplicate_update_fields.append(each)
        for col, val in kwargs.items():
            assert isinstance(val, Column)
            up = ColumnUpdating(Column(self._tables, col), val)
            self._on_duplicate_update_fields.append(up)
        return self

    def sql(self, placeholder="%s"):
        if isinstance(self._sub_query, Select):
            sub_query_sql, sub_query_args = self._sub_query.sql(placeholder)
        elif isinstance(self._sub_query, _SubQueryTable):
            sub_query_sql, sub_query_args = self._sub_query.from_view(placeholder)
        else:
            raise ValueError("Unknown")
        sql_pieces = ["INSERT INTO {table}({fields}) {sub_query}".format(table=self._tables.raw_view,
                                                                         fields=", ".join(field.insert_view for field in
                                                                                          self._fields),
                                                                         sub_query=sub_query_sql)]
        if self._on_duplicate_update_fields:
            # sql_pieces.append("ON DUPLICATE KEY UPDATE {}".format(
            #     ", ".join("{}={}".format(pair.field.insert_view, pair.value.where_view) for pair in self._on_duplicate_update_fields)))
            ts = []
            update_args = []
            for each in self._on_duplicate_update_fields:
                s, a = each.sql(placeholder)
                ts.append(s)
                update_args.extend(a)
            sql_pieces.append("ON DUPLICATE KEY UPDATE {}".format(
                ", ".join(ts)
            ))
            sub_query_args.extend(update_args)
        return " ".join(sql_pieces), sub_query_args


class Update(_Query):
    def __init__(self, table, *pairs, **pairs_kwargs):
        assert isinstance(table, Table)
        super(Update, self).__init__(tables=table)
        assert len(pairs) % 2 == 0
        self._where = None
        self._pairs = []
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is table
            self._pairs.append(ColumnUpdating(key, val))
        for key, val in pairs_kwargs.items():
            self._pairs.append(ColumnUpdating(getattr(table, key), val))

    def where(self, cond):
        assert cond is None or isinstance(cond, _Where)
        self._where = cond
        return self

    def add_fields(self, *pairs, **pairs_kwargs):
        assert len(pairs) % 2 == 0
        for cursor in range(0, len(pairs), 2):
            key, val = pairs[cursor:cursor + 2]
            assert isinstance(key, Column)
            assert key.table is None or key.table is self._tables
            self._pairs.append(ColumnUpdating(key, val))
        for key, val in pairs_kwargs.items():
            self._pairs.append(ColumnUpdating(getattr(self._tables, key), val))
        return self

    def update(self, *updating):
        for each in updating:
            assert isinstance(each, ColumnUpdating)
            self._pairs.append(each)
        return self

    def sql(self, placeholder="%s"):
        args = []
        update_pieces = []
        for each in self._pairs:
            s, a = each.sql(placeholder)
            update_pieces.append(s)
            args.extend(a)
        sql_pieces = ["UPDATE {} SET {}".format(self._tables.raw_view,
                                                ", ".join(update_pieces))]
        if self._where and not self._where.is_empty():
            where_clause, where_args = self._where.sql(placeholder)
            sql_pieces.append("WHERE {}".format(where_clause))
            args.extend(where_args)
        return " ".join(sql_pieces), args


class Select(_Query):
    def __init__(self, tables, fields=None, where=None, sort=None, group=None, offset=0, count=0):
        super(Select, self).__init__(tables)
        assert fields is None or (isinstance(fields, (list, tuple)))
        self._fields = []
        if fields:
            for field in fields:
                if isinstance(field, basestring):
                    self._fields.append(RawSQLField(field))
                else:
                    assert isinstance(field, _Column)
                    self._fields.append(field)
        assert where is None or isinstance(where, _Where)
        assert sort is None or isinstance(sort, Sort)
        assert group is None or isinstance(group, GroupBy)
        assert offset >= 0
        assert count >= 0
        self._where = where
        self._sort = sort
        self._group = group
        self._offset = offset
        self._count = count

    def __getitem__(self, item):
        if not isinstance(item, slice):
            raise TypeError("select doesn't support")
        assert item.start >= 0
        assert item.stop > item.start
        self._offset = item.start
        self._count = item.stop - item.start
        return self

    def select(self, *fields):
        _fields = []
        for field in fields:
            if isinstance(field, basestring):
                _fields.append(RawSQLField(field))
            else:
                assert isinstance(field, _Column)
                _fields.append(field)
        self._fields = _fields
        return self

    def where(self, cond):
        assert isinstance(cond, _Where)
        self._where = cond
        return self

    def group(self, *cols):
        assert len(cols) > 0
        if len(cols) == 1 and isinstance(cols[0], GroupBy):
            self._group = cols[0]
        else:
            self._group = GroupBy(*cols)
        return self

    def asc(self, column):
        assert isinstance(column, Column)
        assert column.table in self._tables
        if not self._sort:
            self._sort = Sort(column)
        else:
            self._sort.asc(column)
        return self

    def desc(self, column):
        assert isinstance(column, Column)
        assert column.table in self._tables
        if not self._sort:
            self._sort = Sort(column, Sort.DESC)
        else:
            self._sort.desc(column)
        return self

    def as_table(self, alias):
        return _SubQueryTable(alias, self)

    def sql(self, placeholder="%s"):
        sql_pieces = []
        args = []
        fields = self._fields and ", ".join(
            field.field_view for field in self._fields) or "*"
        from_sql, from_args = self._tables.from_view(placeholder)
        sql_pieces.append("SELECT {fields} FROM {tables}".format(fields=fields, tables=from_sql))
        args.extend(from_args)
        if self._where and not self._where.is_empty():
            where_clause, where_args = self._where.sql(placeholder)
            sql_pieces.append("WHERE {where}".format(where=where_clause))
            args.extend(where_args)
        if self._group:
            sql_pieces.append("GROUP BY {}".format(self._group.sql))
        if self._sort:
            sql_pieces.append("ORDER BY {}".format(self._sort.sql))
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

    def sql(self, placeholder="%s"):
        args = []
        from_sql, from_args = self._tables.from_view(placeholder)
        args.extend(from_args)
        sql_pieces = ["DELETE FROM {table}".format(table=from_sql)]
        if self._where and not self._where.is_empty():
            where_clause, where_args = self._where.sql(placeholder)
            sql_pieces.append("WHERE {}".format(where_clause))
            args.extend(where_args)
        return " ".join(sql_pieces), args


if __name__ == "__main__":
    # test here>>>
    """
    class: id, name, access_num
    student: id, name, class_id(class:id), age
    student_snapshot: id, name, class_id, age
    teacher: id, name
    teach: teacher_id(teacher:id), class_id(class:id)
    """
    student = Table("student")
    ss = Table("student_snapshot").as_("snapshot")
    class_ = Table("class").as_("c")
    teacher = Table("teacher")
    teach = Table("teach").as_("ss")
    print(student.select(student.builtin_all).group(student.id, student.age)[4:10].sql())
    print(student.select(student.builtin_all, student.age.max_("max_age")).sql())
    print(student.select(student.builtin_all, student.age.min_("min_age")).sql())
    print(student.select(student.id.count("student_count")).sql())
    print(student.select("id", "age").sql())

    print(
    Select(tables=student.join(class_, (student.class_id == class_.id) & (student.age == 20))).asc(class_.name).sql(
        "?"))
    print(Select(tables=teacher.join(teach,
                                     teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id),
                 where=(class_.id == '123123'), fields=[teacher.builtin_all]).sql())
    print(Select(tables=teacher.join(teach,
                                     teach.teacher_id == teacher.id).join(class_, class_.id == teach.class_id)).where(
        class_.id == None).select(teacher.builtin_all).sql())
    print("=" * 20)
    print(Insert(student, student.id, 1, student.name, "学生a", student.class_id, "21321").on_duplicate_key_fields(
        student.name, "学生a").sql())
    print(
    student.insert(id=1, name="学生a", class_id="21321").on_duplicate_key_fields(name="学生a").add_fields(age=20).sql())

    sub = Select(student).where(student.name == 'test').select(
        student.id, student.name, student.class_id, student.age).as_table("old_student")
    print(ss.insert_from_select([ss.id, ss.name, ss.class_id, ss.age], sub).on_duplicate_key_update(name=sub.name, age=sub.age).sql())

    print(student.update(student.name, "学生").where(student.id == 1).sql())
    print(student.update(name="学生").add_fields(age=20).where(student.id == 1).sql())
    print(Delete(table=student).where(student.id == 1).sql())
    print(Delete(table=teacher).where(teacher.id.in_(
        Select(tables=teach.join(teacher, teach.teacher_id == teacher.id)).select(teacher.id).where(
            (teach.class_id == 2) & (teacher.deleted == 0)))).sql())

    sub_query = student.select(student.age.max_("oldest")).where(student.age <= 20).as_table("sub")
    print(student.inner_join(sub_query, sub_query.oldest == student.age).select().sql())

    cond = EmptyCond()
    cond |= (student.name == '12321') | (student.name == '23123')
    cond &= student.age >= 20
    query = student.select().where(cond)
    print(query.sql())
    print(class_.update().update(class_.access_num.inc()).sql())

    stat = ss.select(ss.age, RawSQLField("group_concat(name ORDER BY name) AS names"))
    print(stat.sql())


