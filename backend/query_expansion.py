try:
    from nltk.corpus import wordnet
except ImportError:
    wordnet = None
    print('NLTK tidak terinstall. Fitur query expansion WordNet tidak aktif.')

def expand_query(query: str) -> list:
    if wordnet is None:
        return []
    synonyms = set()
    for syn in wordnet.synsets(query):
        if syn is not None:
            for lemma in syn.lemmas():
                synonyms.add(lemma.name())
    return list(synonyms) if synonyms else [query]

# Jika muncul error import nltk.corpus, pastikan sudah pip install nltk dan nltk-data. Jika environment tidak ada nltk, warning ini bisa diabaikan untuk deployment yang tidak butuh fitur query expansion. 