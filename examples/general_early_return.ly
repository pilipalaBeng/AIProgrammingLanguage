fn classify(value: int) -> int {
    if value < 0 {
        return -1
    }
    if value == 0 {
        return 0
    }
    return 1
}

fn stable_value(ready: bool) -> int {
    while true {
        if ready {
            return 7
        } else {
            return 8
        }
    }
}

fn main() {
    print(classify(-2))
    print(classify(0))
    print(classify(3))
    print(stable_value(true))
    print(stable_value(false))
}
