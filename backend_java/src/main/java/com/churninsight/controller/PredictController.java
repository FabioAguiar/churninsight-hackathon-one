package com.churninsight.controller;

import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import com.churninsight.service.PredictService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/predict")
@CrossOrigin(origins = "*")
public class PredictController {

    private static final Logger logger = LoggerFactory.getLogger(PredictController.class);
    private final PredictService predictService;

    public PredictController(PredictService predictService) {
        this.predictService = predictService;
    }

    @PostMapping
    public ResponseEntity<PredictResponseDTO> predict(@RequestBody @Valid PredictRequestDTO request) {

        logger.info("Recebendo previsão de churn. Contrato: {}", request.getContract());

        PredictResponseDTO response = predictService.predict(request);

        logger.info("Previsão realizada com sucesso: {}", response.getProbabilidade());

        return ResponseEntity.ok(response);
    }
}