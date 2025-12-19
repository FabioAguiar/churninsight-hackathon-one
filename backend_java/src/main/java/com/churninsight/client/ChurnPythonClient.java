package com.churninsight.client;

import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

// A mudança está aqui: lê do application.properties em vez de ser fixo
@FeignClient(name = "churn-python-api", url = "${churn.python.api.url}")
public interface ChurnPythonClient {

    @PostMapping("/predict")
    PredictResponseDTO preverChurn(@RequestBody PredictRequestDTO request);
}