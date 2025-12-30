package com.churninsight.dto;

import com.churninsight.model.enums.ContractType;
import com.churninsight.model.enums.InternetServiceType;
import com.churninsight.model.enums.PaymentMethodType;
import com.churninsight.model.enums.YesNo;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PredictRequestDTO {

    @NotNull(message = "O tempo de contrato (tenure) é obrigatório")
    @Min(value = 0, message = "O tempo de contrato não pode ser negativo")
    private Integer tenure;

    @NotNull(message = "O tipo de contrato é obrigatório")
    private ContractType contract;

    @JsonProperty("internet_service")
    @NotNull(message = "O serviço de internet é obrigatório")
    private InternetServiceType internetService;

    @JsonProperty("online_security")
    @NotNull(message = "A segurança online é obrigatória")
    private YesNo onlineSecurity;

    @JsonProperty("tech_support")
    @NotNull(message = "O suporte técnico é obrigatório")
    private YesNo techSupport;

    @JsonProperty("monthly_charges")
    @NotNull(message = "A cobrança mensal é obrigatória")
    private Double monthlyCharges;

    @JsonProperty("paperless_billing")
    @NotNull(message = "A opção de conta digital é obrigatória")
    private YesNo paperlessBilling;

    @JsonProperty("payment_method")
    @NotNull(message = "O método de pagamento é obrigatório")
    private PaymentMethodType paymentMethod;
}