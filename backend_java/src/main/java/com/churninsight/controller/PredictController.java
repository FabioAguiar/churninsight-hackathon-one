package com.churninsight.controller;


import com.churninsight.dto.PredictRequestDTO;
import com.churninsight.dto.PredictResponseDTO;
import com.churninsight.service.PredictService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/predict")
public class PredictController {

    private final PredictService predictService;


    public PredictController(PredictService predictService) {
        this.predictService = predictService;
    }


    @PostMapping
    public ResponseEntity<PredictResponseDTO> predict(
            @RequestBody @Valid PredictRequestDTO request) {

        PredictResponseDTO response = predictService.predict(request);
        return  ResponseEntity.ok(response);

    }
}