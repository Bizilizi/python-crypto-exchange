import operator
import typing as t


T = t.TypeVar("T")


def bisect_left(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
    reversed: bool = False,
) -> int:
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if reversed:
        op = operator.gt
    else:
        op = operator.lt

    if lo < 0:
        raise ValueError("lo must be non-negative")
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if op(key(a[mid]), key(x)):
            lo = mid + 1
        else:
            hi = mid
    return lo


def bisect_right(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
    reversed: bool = False,
) -> int:
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if reversed:
        op = operator.gt
    else:
        op = operator.lt

    if lo < 0:
        raise ValueError("lo must be non-negative")
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if op(key(x), key(a[mid])):
            hi = mid
        else:
            lo = mid + 1
    return lo


def reverse_insort(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
) -> None:
    """Insert item x in list a, and keep it reverse-sorted assuming it is reverse-sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    lo = bisect_right(a, x, lo, hi, key, reversed=True)
    a.insert(lo, x)


def left_reverse_insort(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
) -> None:
    """Insert item x in list a, and keep it reverse-sorted assuming it is reverse-sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    lo = bisect_left(a, x, lo, hi, key, reversed=True)
    a.insert(lo, x)


def insort(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
) -> None:
    """Insert item x in list a, and keep it sorted assuming it is sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    lo = bisect_right(a, x, lo, hi, key)
    a.insert(lo, x)


def left_insort(
    a: t.List[T],
    x: T,
    lo: int = 0,
    hi: t.Optional[int] = None,
    key: t.Callable[..., t.Any] = lambda el: el,
) -> None:
    """Insert item x in list a, and keep it sorted assuming it is sorted.

    If x is already in a, insert it to the left of the leftmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    lo = bisect_left(a, x, lo, hi, key)
    a.insert(lo, x)
