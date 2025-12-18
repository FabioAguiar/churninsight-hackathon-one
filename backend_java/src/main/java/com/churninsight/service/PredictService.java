package com.churninsight.service;

import com.churninsight.client.ChurnPythonClient;
import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import org.springframework.stereotype.Service;

@Service
public class PredictService {

    private final ChurnPythonClient pythonClient;

    public PredictService(ChurnPythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    public PredictResponseDTO predict(PredictRequestDTO dto) {
        return pythonClient.preverChurn(dto);
    }
}