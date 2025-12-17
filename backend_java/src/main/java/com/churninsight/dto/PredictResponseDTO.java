package com.churninsight.dto;

public class PredictResponseDTO {

    private boolean churn;
    private double provability;

    public PredictResponseDTO(boolean churn, double provability){
        this.churn = churn;
        this.provability = provability;
    }

    public boolean isChurn() {
        return churn;
    }

    public double getProvability() {
        return provability;
    }
}
