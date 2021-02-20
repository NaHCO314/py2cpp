import ast


def priority(op):
    if type(op) in (ast.UnaryOp, ast.BinOp):
        op = type(op.op)

    else:
        op = type(op)

    if op == ast.Lambda:
        return 0

    elif op == ast.IfExp:
        return 1

    elif op == ast.Or:
        return 2

    elif op == ast.And:
        return 3

    elif op == ast.Not:
        return 4

    elif issubclass(op, ast.cmpop):
        return 5

    elif op == ast.BitOr:
        return 6

    elif op == ast.BitXor:
        return 7

    elif op == ast.BitAnd:
        return 8

    elif op in (ast.LShift, ast.RShift):
        return 9

    elif op in (ast.Add, ast.Sub):
        return 10

    elif op in (ast.Mult, ast.MatMult, ast.Div, ast.FloorDiv, ast.Mod):
        return 11

    elif issubclass(op, ast.unaryop):
        return 12

    else:
        return 13


def to_func(func):
    func_map = {ast.Is: "py_is", ast.IsNot: "py_is_not", ast.In: "py_in",
                ast.NotIn: "py_not_in", ast.Pow: "pow"}
    return func_map[func]


def Const_Name(term):
    if type(term) == ast.Constant:
        term = term.value
        if str == type(term):
            return f'"{term}"s'
        else:
            return f"{term}"

    elif ast.Name == type(term):
        return f"{term.id}"


def UnaryOp(term):
    op_map = {ast.UAdd: "+", ast.USub: "-", ast.Not: "not ", ast.Invert: "~"}
    op, operand = term.op, term.operand
    operand_eval = cpp_eval(operand)

    if priority(operand) != 13:
        operand_eval = f"({operand_eval})"

    return f"{op_map[type(op)]}{operand_eval}"


def BinOp(formula):
    op, left, right = formula.op, formula.left, formula.right
    left_eval, right_eval = cpp_eval(left), cpp_eval(right)
    op_map = {ast.Add: "+",
              ast.Sub: "-",
              ast.Mult: "*",
              ast.Mod: "%",
              ast.LShift: "<<",
              ast.RShift: ">>",
              ast.BitOr: "|",
              ast.BitXor: "^",
              ast.BitAnd: "&",
              }
    not_associativity = {ast.Sub, ast.Div, ast.Mod, ast.LShift, ast.RShift}

    # 割り算は処理がめんどくさいのではじく
    # ToDo: 自明にintかdoubleな場合を分ける
    if type(op) == ast.Div:
        return f"double({left_eval}) / double({right_eval})"
    elif type(op) == ast.FloorDiv:
        return f"int({left_eval}) / int({right_eval})"

    # 関数で処理する演算をはじく
    if type(op) not in op_map:
        return f"{to_func(type(op))}({left_eval}, {right_eval})"

    # その他
    left_priority = priority(left)
    right_priority = priority(right)

    # 左辺の優先順位がこの演算より低ければ()をつける
    if left_priority < priority(op):
        left_eval = f"({left_eval})"

    # 右辺の優先順位がこの演算より低いか、同じで結合律を満たさないなら()を付ける
    if right_priority < priority(op) \
            or (right_priority == priority(op) and type(op) in not_associativity):
        right_eval = f"({right_eval})"

    return f"{left_eval} {op_map[type(op)]} {right_eval}"


def BoolOp(formula):
    op, values = formula.op, formula.values
    op_map = {ast.Or: "or", ast.And: "and"}
    result = ""

    # すべての要素に対して処理する
    for i in range(len(values)):
        value = values[i]
        value_eval = cpp_eval(value)

        # 項の優先順位がこの演算より低ければ()をつける
        if priority(value) < priority(op):
            value_eval = f"({value_eval})"
        result += f"{value_eval}"

        # 最後の要素じゃなければ、演算子をつける
        if i != len(values) - 1:
            result += f" {op_map[type(op)]} "

    return result


def Compare(formula):
    left, ops, comparators = formula.left, formula.ops, formula.comparators
    op_map = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">",
              ast.GtE: ">="}
    result = f"{cpp_eval(left)}"
    if priority(left) < priority(ops[0]):
        result = f"({result})"
    # 処理を簡潔にするためにcomparatorsの最後にleftをつける
    comparators += [left]

    # すべての要素について処理する
    for i in range(len(ops)):
        value_eval = cpp_eval(comparators[i])
        # 項の優先順位がこの演算より低ければ()をつける
        if priority(comparators[i]) < priority(ops[i]):
            value_eval = f"({value_eval})"

        # 結果に足す
        if type(ops[i]) in op_map:
            result += f" {op_map[type(ops[i])]} {value_eval}"

        # is、is not、in、not inはC++にないので別処理
        else:
            result += " and "

            # 最初の項なら、resultを初期化する
            if i == 0:
                result = ""

            # 関数をつける
            left, right = cpp_eval(comparators[i-1]), cpp_eval(comparators[i])
            result += f"{to_func(type(ops[i]))}({left}, {right})"

            # 最後じゃなく、かつ次の演算が特殊ケースじゃないならandをつける
            if i != len(ops) - 1 and type(ops[i+1]) in op_map:
                result += f" and {value_eval}"

    return result


def Attribute(attr):
    value, attr, ctx = cpp_eval(attr.value), attr.attr, attr.ctx

    # 特殊なケースをはじく
    # 今のところ、特殊なケースを知らない

    return f"{value}.{attr}"


def IfExp(exp):
    test, body, orelse = exp.test, exp.body, exp.orelse
    test_eval, body_eval, orelse_eval = cpp_eval(test), cpp_eval(body), cpp_eval(orelse)
    # それぞれの要素について、優先順位が三項演算子以下か確認し、そうなら()をつける
    # 三項演算子の優先順位は2
    if priority(test) <= 2:
        test_eval = f"({test_eval})"
    if priority(body) <= 2:
        body_eval = f"({body_eval})"
    if priority(orelse) <= 2:
        orelse_eval = f"({orelse_eval})"

    return f"{test_eval} ? {body_eval} : {orelse_eval}"


def NamedExpr(exp):
    target, value = cpp_eval(exp.target), cpp_eval(exp.value)
    return f"({target}={value})"


def cpp_eval(formula):
    # 式が変数か定数の場合
    if type(formula) in (ast.Constant, ast.Name):
        return Const_Name(formula)

    elif type(formula) == ast.UnaryOp:
        return UnaryOp(formula)

    elif type(formula) == ast.BinOp:
        return BinOp(formula)

    elif type(formula) == ast.BoolOp:
        return BoolOp(formula)

    elif type(formula) == ast.Compare:
        return Compare(formula)

    elif type(formula) == ast.Attribute:
        return Attribute(formula)

    elif type(formula) == ast.IfExp:
        return IfExp(formula)

    elif type(formula) == ast.NamedExpr:
        return NamedExpr(formula)
