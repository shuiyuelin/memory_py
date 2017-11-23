from queue import Queue
import argparse
import traceback
import urllib
import time
import logging
from datetime import datetime

from flask import Flask
from flask import request
import json
from tqdm import tqdm
# from lru import LRU

# pickle
from graph.belief_graph import Graph
from kernel_2.main_kernel import MainKernel

import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandfatherdir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parentdir)
sys.path.append(grandfatherdir)

current_date = time.strftime("%Y.%m.%d")
logging.basicConfig(filename=os.path.join(parentdir, 'logs/log_corpus_error_' + current_date + '.log')
                    ,format='%(asctime)s %(message)s', datefmt='%Y.%m.%dT%H:%M:%S', level=logging.INFO)

app = Flask(__name__)

config = {"belief_graph": parentdir + "/model/graph/belief_graph.pkl",
              "solr.facet": 'on',
              "metadata_dir": os.path.join(parentdir, 'model/dmn/dmn_processed/metadata_word.pkl'),
              "data_dir": os.path.join(parentdir, 'model/dmn/dmn_processed/data_word.pkl'),
              "ckpt_dir": os.path.join(parentdir, 'model/dmn/ckpt_word'),
              "gbdt_model_path": parentdir + '/model/ml/belief_clk.pkl',
              "render_api_file": os.path.join(parentdir, 'model/render_2/render_api.txt'),
              "render_location_file": os.path.join(parentdir, 'model/render_2/render_location.txt'),
              "render_recommend_file": os.path.join(parentdir, 'model/render_2/render_recommend.txt'),
              "render_ambiguity_file": os.path.join(parentdir, 'model/render_2/render_ambiguity_removal.txt'),
              "render_price_file": os.path.join(parentdir, 'model/render_2/render_price.txt'),
              "faq_ad": os.path.join(parentdir, 'model/ad_2/faq_ad_anchor.txt'),
              "location_ad": os.path.join(parentdir, 'model/ad_2/category_ad_anchor.txt'),
              "clf": 'dmn',  # or memory
              "shuffle":False
              }

kernel = MainKernel(config)
# https://pypi.python.org/pypi/lru-dict/
lru_kernels = dict()

QSIZE = 1
kernel_backups = Queue(1000)


@app.route('/e/info', methods=['GET', 'POST'])
def info():
    size = len(lru_kernels)
    result = {"question": "request info", "result": {"answer": size}, "user": "solr"}
    return json.dumps(result, ensure_ascii=False)

# @app.route('/e/log', methods=['GET', 'POST'])
# def info():
#     size = len(lru_kernels)
#     result = {"question": "request info", "result": {"answer": size}, "user": "solr"}
#     return json.dumps(result, ensure_ascii=False)


@app.route('/e/chat', methods=['GET', 'POST'])
def chat():
    try:
        args = request.args
        q = args['q']
        q = urllib.parse.unquote(q)
        u = 'solr'
        if 'u' in args:
            u = args['u']
            if u not in lru_kernels:
                if kernel_backups.qsize() > 0:
                    ek = kernel_backups.get_nowait()
                    lru_kernels[u] = ek
                else:
                    result = {"question": q,
                              "result": {"answer": "maximum user reached hence rejecting request"}, "user": u}
                    return json.dumps(result, ensure_ascii=False)
            u_i_kernel = lru_kernels[u]
            r = u_i_kernel.kernel(q=q, user=u)
            result = {"question": q, "result": {"answer": r}, "user": u}
            return json.dumps(result, ensure_ascii=False)

        else:
            r = kernel.kernel(q=q)
            result = {"question": q, "result": {"answer": r}, "user": "solr"}
            return json.dumps(result, ensure_ascii=False)
    except Exception:
        logging.error("C@user:{}##error_details:{}".format(u, traceback.format_exc()))
        result = {"question": q, "result": {"answer": "kernel exception"}, "user": "solr"}
        return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    # SK = SceneKernel()
    # print(SK.kernel('你叫什么名字'))

    parser = argparse.ArgumentParser()
    parser.add_argument('--qsize', choices={'1', '20', '200'},
                        default='200', help='q_size initializes number of the starting instances...')
    args = parser.parse_args()

    QSIZE = int(args.qsize)

    for i in tqdm(range(QSIZE)):
        k = MainKernel(config)
        kernel_backups.put_nowait(k)
    print('web started...')
    app.run(host='0.0.0.0', port=21304, threaded=True)