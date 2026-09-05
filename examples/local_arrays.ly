fn add(a: int, b: int) -> int {
    return a + b
}

fn show_arrays(index: int) {
    let scores: int[] = [90, add(90, 5), 100]
    let names: string[] = ["LAI", "LingYu"]
    let flags: bool[] = [true, scores[0] > 80]
    let empty: int[] = []
    print(scores[index])
    print(names[0])
    print(flags[1])
}

fn main() {
    show_arrays(1)
}
