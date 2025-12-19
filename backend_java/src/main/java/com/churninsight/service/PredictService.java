package com.churninsight.service;

import com.churninsight.client.ChurnPythonClient;
import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import feign.FeignException;
import feign.RetryableException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class PredictService {

    private final ChurnPythonClient pythonClient;

    public PredictService(ChurnPythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    public PredictResponseDTO predict(PredictRequestDTO requestDTO) {
        try {
            return pythonClient.preverChurn(requestDTO);

        } catch (RetryableException e) {
            System.err.println("Erro crítico: Python offline ou timeout.");
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Serviço de IA indisponível.");

        } catch (FeignException e) {
            System.err.println("Erro do Python: " + e.contentUTF8());
            throw new ResponseStatusException(HttpStatus.valueOf(e.status()), "Erro na análise de IA: " + e.contentUTF8());

        } catch (Exception e) {
            e.printStackTrace();
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Erro interno ao processar previsão.");
        }
    }
}