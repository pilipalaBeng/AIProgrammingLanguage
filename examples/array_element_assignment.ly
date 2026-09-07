fn update_scores() {
    let scores: int[] = [90, 95, 100]
    scores[0] = 80
    scores[0] += 5
    scores[1] -= 5
    scores[1] *= 2
    scores[1] /= 3
    scores[2] %= 30
    for i from 0 to 3 {
        print(scores[i])
    }
}

fn update_labels() {
    let names: string[] = ["before"]
    let flags: bool[] = [false]
    names[0] = "after"
    flags[0] = true
    print(names[0])
    print(flags[0])
}

fn main() {
    update_scores()
    update_labels()
}
