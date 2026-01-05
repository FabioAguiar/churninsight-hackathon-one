package com.churninsight.service;

import com.churninsight.client.ChurnPythonClient;
import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import feign.FeignException;
import feign.RetryableException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class PredictService {

    private static final Logger logger = LoggerFactory.getLogger(PredictService.class);

    private final ChurnPythonClient pythonClient;

    public PredictService(ChurnPythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    public PredictResponseDTO predict(PredictRequestDTO requestDTO) {

        try {
            return pythonClient.preverChurn(requestDTO);

        } catch (RetryableException e) {

            logger.error("Timeout ou falha de conexão com FastAPI: {}", e.getMessage());
            System.err.println("Erro crítico: Python offline ou timeout.");
            throw new ResponseStatusException(
                    HttpStatus.GATEWAY_TIMEOUT,
                    "Serviço de IA indisponível no momento. Tente novamente mais tarde."
            );

        } catch (FeignException e) {

            logger.error("FastAPI retornou erro {}: {}", e.status(), e.contentUTF8());
            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "Erro ao processar análise de IA."
            );

        } catch (Exception e) {
            logger.error("Erro inesperado no serviço de previsão", e);
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "Erro interno ao processar previsão."
            );
        }
    }
}