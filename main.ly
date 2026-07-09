fn greet() {
    print("Hello from function")
}

fn show_math() {
    let count = 1 + 2
    print(count)
    let ready = count == 3
    if ready {
        print("count is three")
    }
}

fn show_profile(name: string, count: int, ready: bool) {
    print(name)
    print(count)
    print(ready)
}

fn add(a: int, b: int) -> int {
    return a + b
}

fn label() -> string {
    return "Return label"
}

fn is_ready(count: int) -> bool {
    return count == 7
}

fn grade(score: int) -> string {
    if score > 90 {
        return "A"
    } else if score > 80 {
        return "B"
    } else {
        return "C"
    }
}

fn first_over_two(limit: int) -> int {
    let count = 0
    while count < limit {
        if count > 2 {
            return count
        }
        count = count + 1
    }
    return limit
}

fn main() {
    // LAI v0.18 demo
    print("Hello LAI")
    let name = "JD"
    print(name)
    greet()
    show_math()
    show_profile("Param JD", 7, true)
    let total = add(3, 4)
    print(total)
    print(label())
    print(grade(85))
    print(first_over_two(5))
    for i from 0 to 3 {
        print(i)
    }
    let loop = 0
    while loop < 3 {
        print(loop)
        loop = loop + 1
    }
    let control = 0
    while control < 5 {
        control = control + 1
        if control < 2 {
            continue
        }
        print(control)
        if control > 2 {
            break
        }
    }
    if is_ready(total) {
        print("return bool works")
    }
    if 1 < 2 {
        print("math works")
    }
    if false {
        print("unexpected")
    } else if true {
        print("else if works")
    } else {
        print("else fallback")
    }
}
