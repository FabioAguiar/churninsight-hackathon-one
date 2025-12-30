package com.churninsight.client;

import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;


@FeignClient(name = "churn-python-api", url = "${churn.python.api.url}")
public interface ChurnPythonClient {

    @PostMapping("/predict")
    PredictResponseDTO preverChurn(@RequestBody PredictRequestDTO request);
}