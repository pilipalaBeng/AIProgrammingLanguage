fn trace(value: bool) -> bool {
    print(99)
    return value
}

fn main() {
    let count = 3
    print(count > 0 and count < 5)
    print(false or true and false)
    print(not count == 0)
    print(not not true)
    print((false or true) and true)
    print(false and trace(true))
    print(true or trace(false))
}
