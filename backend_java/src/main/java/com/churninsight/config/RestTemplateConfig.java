package com.churninsight.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class RestTemplateConfig {

    /**
     * Esse RestTemplate será usado para chamar o FastAPI.
     * Aqui definimos timeouts explícitos para:
     * - Tempo máximo para CONECTAR
     * - Tempo máximo para ESPERAR RESPOSTA
     * Assim evitamos travamentos indefinidos na API Java.
     */

    @Bean
    public RestTemplate restTemplate(
            @Value("${churn.python.api.timeout-ms:5000}") int timeout) {

        SimpleClientHttpRequestFactory factory =
                new SimpleClientHttpRequestFactory();

        // Tempo máximo para abrir conexão
        factory.setConnectTimeout(timeout);

        // Tempo máximo esperando resposta do FastAPI
        factory.setReadTimeout(timeout);

        return new RestTemplate(factory);
    }


}
