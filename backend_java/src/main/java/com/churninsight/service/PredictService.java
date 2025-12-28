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

    /**
     * Implementação resiliente:
     * - Timeout / indisponível  -> 503
     * - Erro retornado pelo FastAPI -> 502
     * - Erro inesperado -> 500
     * Sem expor detalhes internos do serviço Python.
     */
    public PredictResponseDTO predict(PredictRequestDTO requestDTO) {

        try {
            return pythonClient.preverChurn(requestDTO);

        } catch (RetryableException e) {
            // Timeout, serviço fora do ar, conexão recusada
            System.err.println("Erro crítico: Python offline ou timeout.");
            throw new ResponseStatusException(
                    HttpStatus.SERVICE_UNAVAILABLE,
                    "Serviço de IA indisponível no momento. Tente novamente mais tarde."
            );

        } catch (FeignException e) {
            // FastAPI respondeu algo (400, 422, 500, etc.)
            System.err.println("Erro do serviço Python: " + e.getMessage());
            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "Erro ao processar análise de IA."
            );

        } catch (Exception e) {
            // Erro inesperado nunca deve derrubar a API
            e.printStackTrace();
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "Erro interno ao processar previsão."
            );
        }
    }
}