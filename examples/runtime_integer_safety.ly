fn add_safely(left: int, right: int) -> int {
    return left + right
}

fn show_range(start: int, end: int, interval: int) {
    for value from start through end step interval {
        print(value)
    }
}

fn main() {
    print(add_safely(20, 22))
    show_range(2147483646, 2147483647, 1)
}
