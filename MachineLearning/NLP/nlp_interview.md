# NLP interview question and answer

### 1. Natural Language Processing (NLP):

is a key area in artificial intelligence that enables computers to understand, interpret, and respond to human language. The subfield of Artificial intelligence and computational linguistics deals with the interaction between computers and human languages.

### 2. What are the main challenges in NLP?

The primary challenges in NLP are as follows:

- Semantics and Meaning: It is a difficult undertaking to accurately capture the meaning of words, phrases, and sentences.
- Ambiguity: Language is ambiguous by nature, with words and phrases sometimes having several meanings depending on context.
- Contextual Understanding: Context is frequently used to interpret language. For NLP models to accurately interpret and produce meaningful replies, the context must be understood and used.
- Language Diversity: NLP must deal with the world’s wide variety of languages and dialects, each with its own distinctive linguistic traits, lexicon, and grammar.
- Real-world Understanding: NLP models often fail to understand real-world knowledge and common sense, which humans are born with. Capturing and implementing this knowledge into NLP systems is a continuous problem.

### 3. What are the different tasks in NLP?

Some of the most important tasks in NLP are as follows:

- Text Classification
- Named Entity Recognition (NER)
- Part-of-Speech Tagging (POS)
- Sentiment Analysis
- Language Modeling
- Machine Translation
- Chatbots
- Text Summarization
- Information Extraction
- Text Generation
- Speech Recognition

### 6. What are some common pre-processing techniques used in NLP?

The purpose of preprocessing is to clean and change text data so that it may be processed or analyzed later. Preprocessing in NLP typically involves a series of steps, which may include:

- Tokenization: is the process of breaking down text or string into smaller units. These tokens can be words, characters, or subwords depending on the specific applications.
  - Sentence tokenization: the text is broken down into individual sentences.
  - Word tokenization: the text is simply broken down into words.
  - SubWord tokenization: the text is broken down into subwords. for example, Subword i.e Sub+ word.
  - Char-label tokenization
- Stop Word Removal
- Text Normalization: also known as text standardization, is the process of transforming text data into a standardized or normalized form It involves applying a variety of techniques to ensure consistency, reduce variations, and simplify the representation of textual information.

  - Lowercasing
  - Lemmatization: Converting words to their base or dictionary form, known as lemmas. For example, converting “running” to “run” or “better” to “good.”
  - Stemming: Reducing words to their root form by removing suffixes or prefixes. For example, converting “playing” to “play” or “cats” to “cat.”
  - Abbreviation Expansion: Expanding abbreviations or acronyms to their full forms. For example, converting “NLP” to “Natural Language Processing.”
  - Date and Time Normalization

- Removal of Special Characters and Punctuation
- Removing HTML Tags or Markup
- Spell Correction
- Sentence Segmentation

### 4. What do you mean by Corpus in NLP?

In NLP, a corpus is a huge collection of texts or documents. It is a structured dataset that acts as a sample of a specific language, domain, or issue. A corpus can include a variety of texts, including books, essays, web pages, and social media posts.

### 5. What do you mean by text augmentation in NLP and what are the different text augmentation techniques in NLP?

Text augmentation in NLP refers to the process that generates new or modified textual data from existing data in order to increase the diversity and quantity of training samples.

- Synonym Replacement
- Random Insertion/Deletion: Randomly inserting or deleting words in the text to simulate noisy or incomplete data and enhance model robustness.
- Word Swapping: Exchanging the positions of words within a sentence to generate alternative sentence structures.
- Back translation: Translating the text into another language and then translating it back to the original language to introduce diverse phrasing and sentence constructions.
- Random Masking: Masking or replacing random words in the text with a special token, akin to the approach used in masked language models like BERT.

### 9. What is NLTK

NLTK stands for Natural Language Processing Toolkit. It offers tokenization, stemming, lemmatization, POS tagging, Named Entity Recognization, parsing, semantic reasoning, and classification.

### 12. What is named entity recognition in NLP?

Named Entity Recognization (NER) is a task in natural language processing that is used to identify and classify the named entity in text. Named entity refers to real-world objects or concepts, such as persons, organizations, locations, dates, etc.

### 16. What is the bag-of-words model?

is a classical text representation technique in NLP that describes the occurrence of words within a document or not. It just keeps track of word counts and ignores the grammatical details and the word order.

### 15. What do you mean by vector space in NLP?

is a mathematical vector where words or documents are represented by numerical vectors form. The word or document’s specific features or attributes are represented by one of the dimensions of the vector. Vector space models are used to convert text into numerical representations that machine learning algorithms can understand.

### 18. What is the term frequency-inverse document frequency (TF-IDF)?

is a classical text representation technique in NLP that uses a statistical measure to evaluate the importance of a word in a document relative to a corpus of documents. It is a combination of two terms: term frequency (TF) and inverse document frequency (IDF).

- Term Frequency (TF): Term frequency measures how frequently a word appears in a document. it is the ratio of the number of occurrences of a term or word (t ) in a given document (d) to the total number of terms in a given document (d). A higher term frequency indicates that a word is more important within a specific document.
- Inverse Document Frequency (IDF): Inverse document frequency measures the rarity or uniqueness of a term across the entire corpus. It is calculated by taking the logarithm of the ratio of the total number of documents in the corpus to the number of documents containing the term. it down the weight of the terms, which frequently occur in the corpus, and up the weight of rare terms.

The TF-IDF score is calculated by multiplying the term frequency (TF) and inverse document frequency (IDF) values for each term in a document. The resulting score indicates the term’s importance in the document and corpus.

### cosine similarity and its importance in NLP

is used to compare two vectors that represent text. The degree of similarity is calculated using the cosine of the angle between the document vectors. To compute the cosine similarity between two text document vectors, we often used the following procedures:

- Text Representation: Convert text documents into numerical vectors using approaches like bag-of-words, TF-IDF (Term Frequency-Inverse Document Frequency), or word embeddings like Word2Vec or GloVe.
- Vector Normalization: Normalize the document vectors to unit length. This normalization step ensures that the length or magnitude of the vectors does not affect the cosine similarity calculation.
- Cosine Similarity Calculation: Take the dot product of the normalised vectors and divide it by the product of the magnitudes of the vectors to obtain the cosine similarity.

### 22. What are the various types of machine learning algorithms used in NLP?

Some of them are as follows:

- Naive Bayes: is extensively used in NLP for text classification tasks.
- Support Vector Machines (SVM): is a supervised learning method that can be used for text classification, sentiment analysis, and named entity recognition. Based on the given set of features, SVM finds a hyperplane that splits data points into various classes.
- Decision Trees: are commonly used for tasks such as sentiment analysis, and information extraction.
- Random Forests: are a type of ensemble learning that combines multiple decision trees to improve accuracy and reduce overfitting. They can be applied to the tasks like text classification, named entity recognition, and sentiment analysis.
  -Recurrent Neural Networks (RNN): RNNs are a type of neural network architecture that are often used in sequence-based NLP tasks like language modelling, machine translation, and sentiment analysis.
  -Long Short-Term Memory (LSTM): LSTMs are a type of recurrent neural network that was developed to deal with the vanishing gradient problem of RNN. LSTMs are useful for capturing long-term dependencies in sequences, and they have been used in applications such as machine translation, named entity identification, and sentiment analysis.
- Transformer: Transformers are a relatively recent architecture that has gained significant attention in NLP. By exploiting self-attention processes to capture contextual relationships in text, transformers such as the BERT (Bidirectional Encoder Representations from Transformers) model have achieved state-of-the-art performance in a wide range of NLP tasks.

### 23. What is Sequence Labelling in NLP?

Sequence labelling is one of the fundamental NLP tasks in which, categorical labels are assigned to each individual element in a sequence. Sequence labelling in NLP includes the following tasks.

- Part-of-Speech Tagging (POS Tagging): In which part-of-speech tags (e.g., noun, verb, adjective) are assigned to each word in a sentence.
- Named Entity Recognition (NER)
- Chunking: Words are organized into syntactic units or “chunks” based on their grammatical roles (for example, noun phrase, verb phrase).
- Semantic Role Labeling (SRL): In which, words or phrases in a sentence are labelled based on their semantic roles like Teacher, Doctor, Engineer, Lawyer etc
- Speech Tagging

### 25. What is the GPT?

GPT stands for “Generative Pre-trained Transformer”. It refers to a collection of large language models created by OpenAI. It is trained on a massive dataset of text and code, which allows it to generate text, generate code, translate languages, and write many types of creative content, as well as answer questions in an informative manner. GPT models are built on the Transformer architecture, which allows them to efficiently capture long-term dependencies and contextual information in text.


