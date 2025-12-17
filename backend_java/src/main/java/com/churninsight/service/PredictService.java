package com.churninsight.service;

import com.churninsight.dto.PredictResponseDTO;
import com.churninsight.dto.PredictRequestDTO;
import org.springframework.stereotype.Service;

@Service
public class PredictService {
    public PredictResponseDTO predict(PredictRequestDTO dto) {

        // Preparação dos dados (normalização)
        int tenure = dto.getTenure();
        double monthlyCharges = dto.getMonthlyCharger();
        boolean paperlless = dto.getPaperless_Billinh().equalsIgnoreCase("Yes");
        boolean onlineSecurity = dto.getOnlineSecurity().equalsIgnoreCase("Yes");
        boolean techSupport = dto.getTechSupport().equalsIgnoreCase("Yes");

        // resposta
        boolean churn = monthlyCharges > 80;
        double probability = churn ? 0.85 : 0.15;

        return new PredictResponseDTO(churn, probability);
    }


}
