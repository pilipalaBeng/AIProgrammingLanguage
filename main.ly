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

fn main() {
    // LAI v0.11 demo
    print("Hello LAI")
    let name = "JD"
    print(name)
    greet()
    show_math()
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
