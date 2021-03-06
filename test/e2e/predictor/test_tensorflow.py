# Copyright 2019 kubeflow.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import numpy as np
from kubernetes import client
from kfserving import KFServingClient
from kfserving import constants
from kfserving import V1beta1PredictorSpec
from kfserving import V1beta1TFServingSpec
from kfserving import V1beta1InferenceServiceSpec
from kfserving import V1beta1InferenceService
from kubernetes.client import V1ResourceRequirements

from ..common.utils import predict
from ..common.utils import KFSERVING_TEST_NAMESPACE

KFServing = KFServingClient(config_file=os.environ.get("KUBECONFIG", "~/.kube/config"))


def test_tensorflow_kfserving():
    service_name = 'isvc-tensorflow'
    predictor = V1beta1PredictorSpec(
        min_replicas=1,
        tensorflow=V1beta1TFServingSpec(
            storage_uri='gs://kfserving-samples/models/tensorflow/flowers',
            resources=V1ResourceRequirements(
                requests={'cpu': '1', 'memory': '2Gi'},
                limits={'cpu': '1', 'memory': '2Gi'}
            )
        )
    )

    isvc = V1beta1InferenceService(api_version=constants.KFSERVING_V1BETA1,
                                   kind=constants.KFSERVING_KIND,
                                   metadata=client.V1ObjectMeta(
                                       name=service_name, namespace=KFSERVING_TEST_NAMESPACE),
                                   spec=V1beta1InferenceServiceSpec(predictor=predictor))

    KFServing.create(isvc)
    KFServing.wait_isvc_ready(service_name, namespace=KFSERVING_TEST_NAMESPACE)
    res = predict(service_name, './data/flower_input.json')
    assert(np.argmax(res["predictions"][0].get('scores')) == 0)

    # Delete the InferenceService
    KFServing.delete(service_name, namespace=KFSERVING_TEST_NAMESPACE)
