STOP_WORDS = set(["！", "？", "，", "。", "，", '*',
                  '\t', '?', '(', ')', '!', '~', '“', '”', '《', '》', '+', '-', '='])

import re
import os
import sys
import jieba

import json

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from utils.query_util import tokenize
from utils.translator import Translator
from dmn.char.dmn_plus import Config

config = Config()

grandfatherdir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = grandfatherdir + '/data/memn2n/train/complex/'
CANDID_PATH = grandfatherdir + '/data/memn2n/train/complex/candidates.txt'

jieba.load_userdict(grandfatherdir + '/data/dict/ext1.dic')

from itertools import chain
from six.moves import range, reduce

import numpy as np
import tensorflow as tf

translator = Translator()


def build_vocab_beforehand(vocab_base, vocab_path):
    with open(vocab_base, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    vocab = reduce(lambda x, y: x | y, (set(tokenize(line, char=0))
                                        for line in lines))
    vocab = sorted(vocab)
    # print(vocab)
    extra_list = ['api', 'call', 'slot', 'deny', 'rhetorical', 'general',
                  'brand', 'price', 'ac', 'power', 'fr', 'cool_type', 'phone',
                  'sys', 'feature', 'color', 'memsize', 'size', 'distance',
                  'resolution', 'panel', 'dyson', 'root', 'virtual', 'mode',
                  'energy_lvl', 'connect', 'net', 'rmem', 'mmem', 'people', 'vol', 'width', 'height',
                  'control', 'olec', 'led', 'vr', 'oled', 'tcl', 'lcd', 'oled', 'oppo', 'vivo', 'moto', "1.5", '2.5',
                  'plugin'
                  ]
    for w in extra_list:
        vocab.append(w)
    for i in range(100):
        vocab.append('placeholder' + str(i + 1))
    vocab = sorted(vocab)
    # print(vocab)
    # 0 is reserved
    w2idx = dict((c, i + 1) for i, c in enumerate(vocab))
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False)


def load_candidates(candidates_f):
    candidates, candid2idx, idx2candid = [], {}, {}

    with open(candidates_f) as f:
        for i, line in enumerate(f):
            candid2idx[line.strip()] = i
            idx2candid[i] = line.strip()
            candidates.append(line.strip())

    return candidates, candid2idx, idx2candid


def load_dialog(data_dir, candid_dic, char=1):
    train_file = os.path.join(data_dir, 'train.txt')
    test_file = os.path.join(data_dir, 'test.txt')
    val_file = os.path.join(data_dir, 'val.txt')

    train_data = get_dialogs(train_file, candid_dic, char)
    test_data = get_dialogs(test_file, candid_dic, char)
    val_data = get_dialogs(val_file, candid_dic, char)
    return train_data, test_data, val_data


def get_dialogs(f, candid_dic, char=1):
    '''Given a file name, read the file, retrieve the dialogs, and then convert the sentences into a single dialog.
    If max_length is supplied, any stories longer than max_length tokens will be discarded.
    '''
    with open(f) as f:
        return parse_dialogs_per_response(f.readlines(), candid_dic, char)


def parse_dialogs_per_response(lines, candid_dic, char=1):
    '''
        Parse dialogs provided in the babi tasks format
    '''
    data = []
    context = []
    u = None
    r = None
    # print(candid_dic)
    for line in lines:
        line = line.strip()
        if line:
            if '\t' in line:
                # print(line)
                try:
                    u, r, salt = line.split('\t')
                except:
                    print(line)
                    exit(-1)
                if config.multi_label:
                    a = [candid_dic[single_r] for single_r in r.split(",")]
                else:
                    if r not in candid_dic:
                        continue
                    a = candid_dic[r]
                u = tokenize(u, char=char)
                if config.fix_vocab:
                    r = translator.en2cn(r)
                r = tokenize(r, char=char)
                placeholder = salt == 'placeholder'
                if config.fix_vocab:
                    salt = translator.en2cn(salt)
                salt = tokenize(salt, char=char)

                # print(u)
                # temporal encoding, and utterance/response encoding
                # data.append((context[:],u[:],candid_dic[' '.join(r)]))
                data.append((context[:], u[:], a))
                context.append(u)
                # r = r if placeholder == 'placeholder' else r + salt
                context.append(r)
                # if salt != 'placeholder':
                #     context.append(salt)
        else:
            # clear context
            context = []
    # print(data)
    return data


def build_vocab(data, candidates, memory_size=config.max_memory_size):
    if config.fix_vocab:
        with open(grandfatherdir + '/data/char_table/vocab.txt', 'r') as f:
            vocab = json.load(f)
    else:
        vocab = reduce(lambda x, y: x | y, (set(
            list(chain.from_iterable(s)) + q) for s, q, a in data))
        # vocab2 = reduce(lambda x, y: x | y, (set(candidate)
        #                                      for candidate in candidates))
        vocab2 = reduce(lambda x, y: x | y, (set(tokenize(candidate))
                                             for candidate in candidates))
        vocab |= vocab2
        vocab = sorted(vocab)
        print(vocab)
        # 0 is reserved
    w2idx = dict((c, i + 1) for i, c in enumerate(vocab))
    print(w2idx)
    max_story_size = max(map(len, (s for s, _, _ in data)))
    mean_story_size = int(np.mean([len(s) for s, _, _ in data]))
    sentence_size = max(map(len, chain.from_iterable(s for s, _, _ in data)))
    # candidate_sentence_size = max(map(len, candidates))
    tokenized_candidates = [tokenize(candidate) for candidate in candidates]
    candidate_sentence_size = max(map(len, tokenized_candidates))
    query_size = max(map(len, (q for _, q, _ in data)))
    memory_size = min(memory_size, max_story_size)
    vocab_size = len(w2idx) + 1  # +1 for nil word
    sentence_size = max(query_size, sentence_size)  # for the position

    return {
        'w2idx': w2idx,
        'idx2w': vocab,
        'sentence_size': sentence_size,
        'candidate_sentence_size': candidate_sentence_size,
        'memory_size': memory_size,
        'vocab_size': vocab_size,
        'n_cand': len(candidates)
    }  # metadata


def vectorize_candidates(candidates, word_idx, sentence_size):
    shape = (len(candidates), sentence_size)
    C = []
    # print(shape)
    for i, candidate in enumerate(candidates):
        tokens = tokenize(candidate)
        lc = max(0, sentence_size - len(tokens))
        C.append(
            [word_idx[w] if w in word_idx else 0 for w in tokens] + [0] * lc)
    # print(C)
    return tf.constant(C, shape=shape)


def vectorize_data(data, word_idx, sentence_size, batch_size, candidates_size, max_memory_size):
    """
    Vectorize stories and queries.
    If a sentence length < sentence_size, the sentence will be padded with 0's.
    If a story length < memory_size, the story will be padded with empty memories.
    Empty memories are 1-D arrays of length sentence_size filled with 0's.
    The answer array is returned as a one-hot encoding.
    """
    S = []
    Q = []
    A = []
    data.sort(key=lambda x: len(x[0]), reverse=True)
    # print(data[0])
    for i, (story, query, answer) in enumerate(data):
        if i % batch_size == 0:
            memory_size = max(1, min(max_memory_size, len(story)))
        ss = []
        for i, sentence in enumerate(story, 1):
            ls = max(0, sentence_size - len(sentence))
            ss.append(
                [word_idx[w] if w in word_idx else 0 for w in sentence] + [0] * ls)
        # print(np.asarray(ss).shape)
        # take only the most recent sentences that fit in memory
        ss = ss[::-1][:memory_size][::-1]
        # print(ss)
        # print('ddd')

        # pad to memory_size
        lm = max(0, memory_size - len(ss))
        for _ in range(lm):
            ss.append([0] * sentence_size)
        # print(lm)
        lq = max(0, sentence_size - len(query))
        q = [word_idx[w] if w in word_idx else 0 for w in query] + [0] * lq
        # print(query)
        S.append(np.array(ss))
        Q.append(np.array(q))
        A.append(np.array(answer))
    return S, Q, A


def get_batches(train_data, val_data, test_data, metadata, batch_size):
    '''
    input  : train data, valid data
        metadata : {batch_size, w2idx, sentence_size, num_cand, memory_size}
    output : batch indices ([start, end]); train, val split into stories, ques, answers

    '''
    w2idx = metadata['w2idx']
    sentence_size = metadata['sentence_size']
    memory_size = metadata['memory_size']
    n_cand = metadata['n_cand']

    trainS, trainQ, trainA = vectorize_data(
        train_data, w2idx, sentence_size, batch_size, n_cand, memory_size)
    # print(trainS[0])
    # print(trainQ[0])
    # print(trainA[0])
    valS, valQ, valA = vectorize_data(
        val_data, w2idx, sentence_size, batch_size, n_cand, memory_size)
    testS, testQ, testA = vectorize_data(
        test_data, w2idx, sentence_size, batch_size, n_cand, memory_size)
    n_train = len(trainS)
    n_val = len(valS)
    n_test = len(testS)
    # print("Training Size", n_train)
    # print("Validation Size", n_val)
    # print("Test Size", n_test)
    batches = zip(range(0, n_train - batch_size, batch_size),
                  range(batch_size, n_train, batch_size))

    # package train set
    train = {'s': trainS, 'q': trainQ, 'a': trainA}  # you have a better idea?
    # package validation set
    val = {'s': valS, 'q': valQ, 'a': valA}
    # package test set
    test = {'s': testS, 'q': testQ, 'a': testA}

    return train, val, test, [(start, end) for start, end in batches]


if __name__ == '__main__':
    # candidates, candid2idx, idx2candid = load_candidates()
    # # print(candidates)
    # # print(idx2candid)
    # train_data, test_data, val_data = load_dialog(
    #     data_dir=DATA_DIR,
    #     candid_dic=candid2idx)
    # print(train_data[1])

    # metadata = build_vocab(train_data, candidates)

    # train, val, test, batches = get_batches(
    #     train_data, val_data, test_data, metadata, 16)
    # print(batches)

    # test = ['range', 'api_call_search_category:空调,ac.power:3p,brand:艾美特,ac.mode:冷暖,price:range,ac.type:立柜式',
    #         'api_call_slot_category:冰箱 mabbookair api_call_request_pc.type']
    # for t in test:
    #     print(tokenize(t, True))

    base_vocab = grandfatherdir + '/data/char_table/base_vocab.txt'
    vocab_path = grandfatherdir + '/data/char_table/vocab.txt'
    build_vocab_beforehand(base_vocab, vocab_path)
