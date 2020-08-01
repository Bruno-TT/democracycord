import glob
import time
import random
from collections import Counter, defaultdict

#returns a bool based on whether a string contains a number
def is_number(numstring):
    try:
        int(numstring)
        return True
    except:
        return False

#represents a word in a more normalised way
def normalise_word(word):
    chars_to_remove = [".", "(", ")", '"', "~"]
    for char in chars_to_remove:
        word = word.replace(char, "")

        #if it's a number, replace it with the internal representation
        if is_number(word):
            num=int(word)
            if 0<=num and num<=100:
                word="nnn"
            elif 1900<=num and num<=2050:
                word="nnnn"

    return word.lower()

#split headline into words and normalise words
def headline_to_words(headline):
    words = headline.split()
    words = [normalise_word(word) for word in words]
    words = [word for word in words if word]
    return words


def headline_to_ngram_pairs(headline):
    ngrams = []
    words = headline_to_words(headline)
    n_words = len(words)
    for start in range(n_words):
        end = start + order
        if end >= n_words:
            break
        ngrams.append((tuple(words[start:end]), words[end]))
    return ngrams

#given a list of words, turn it into a headline
def wordlist_to_headline(wordlist):
    outlist = []
    for word in wordlist:

        #replace numerical representations with random numbers
        if word=="nnn":word=str(random.randint(0,100))
        elif word=="nnnn":word=str(random.randint(1950, 2050))

        #if not a number, then randomly capitalize words
        elif random.random() <= cap_prob:
            word = word.upper()
        else:word=word[0].upper()+word[1:]

        outlist.append(word)

    return " ".join(outlist) + ".\n"


#appply the generation algorithm to make a random headline
def get_headline():
    current_ngram = random.choice(initial_ngrams_stratified)
    generated_headline_list = list(current_ngram)

    while choices := following_word_per_ngram[current_ngram]:
        generated_headline_list.append(random.choice(choices))
        current_ngram = tuple(generated_headline_list[-order:])
    return wordlist_to_headline(generated_headline_list)

# raw text files
filepaths = glob.glob("copies/*.txt")
order = 3
cap_prob = 0.3
delay = 3

# scrape all files into one list of headlines
headlines = []
for filepath in filepaths:
    with open(filepath, "r", encoding="utf8") as fh:
        text = fh.read()
        headlines.extend(text.split("\n"))
headlines = list(set(headlines))

# remove headlines less than order words
headlines = [
    headline for headline in headlines if len(headline.split(" ")) >= order + 1
]

print(f"\n{len(headlines)} headlines\n")

# randomise
random.shuffle(headlines)

#for each n gram, we have a dict containing a list of following words after that ngram
following_word_per_ngram = defaultdict(list)
for headline in headlines:
    for ngram, word in headline_to_ngram_pairs(headline):
        following_word_per_ngram[ngram].append(word)

#stratified list of initial ngrams to start generation off
initial_ngrams_stratified = []
for headline in headlines:
    initial_ngrams_stratified.append(
        tuple([normalise_word(word) for word in headline_to_words(headline)][:order])
    )

if __name__ == "__main__":
    while 1:
        print(get_headline())
        time.sleep(delay)

