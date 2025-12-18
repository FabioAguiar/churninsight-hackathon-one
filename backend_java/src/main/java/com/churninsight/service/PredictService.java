package com.churninsight.service;

import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.server.ResponseStatusException;

import java.time.Duration;

@Service
public class PredictService {

    
    @Value("${churn.python.api.url}")
    private String pythonApiUrl;

    private final RestTemplate restTemplate;

    
    public PredictService(RestTemplateBuilder restTemplateBuilder) {
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofSeconds(3)) 
                .setReadTimeout(Duration.ofSeconds(10))   
                .build();
    }

    
    public PredictResponseDTO predict(PredictRequestDTO requestDTO) {
        try {
            System.out.println("Enviando dados para o Python em: " + pythonApiUrl);

            
            ResponseEntity<PredictResponseDTO> response = restTemplate.postForEntity(
                    pythonApiUrl,
                    requestDTO,
                    PredictResponseDTO.class
            );

            
            return response.getBody();

        } catch (ResourceAccessException e) {
            
            System.err.println("Erro crítico: Não foi possível conectar ao serviço Python.");
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Serviço de IA indisponível (Connection Refused).");

        } catch (HttpClientErrorException | HttpServerErrorException e) {
            
            System.err.println("Erro retornado pelo Python: " + e.getResponseBodyAsString());
            throw new ResponseStatusException(e.getStatusCode(), "Erro na análise de IA: " + e.getResponseBodyAsString());

        } catch (Exception e) {
            
            e.printStackTrace();
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Erro interno ao processar previsão.");
        }
    }
}