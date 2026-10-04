/*
 * Lightweight IoT Intrusion Detection System (IDS)
 * Embedded C Implementation
 * 
 * Target: Low-power IoT Gateway & Edge Microcontrollers
 */

#include "ids_rules.h"

int predict_ids(const float* features) {
    /* Condition: Weight <= 28.50000 */
    if (features[0] <= 28.50000f) {
        /* Condition: ack_count <= 4.50000 */
        if (features[1] <= 4.50000f) {
            return 1; /* Attack (1) */
        } else {
            /* Condition: Weight <= 27.50000 */
            if (features[0] <= 27.50000f) {
                /* Condition: Weight <= 25.50000 */
                if (features[0] <= 25.50000f) {
                    return 0; /* Benign (0) */
                } else {
                    /* Condition: ack_count <= 8.00000 */
                    if (features[1] <= 8.00000f) {
                        return 1; /* Attack (1) */
                    } else {
                        /* Condition: IAT <= 0.01314 */
                        if (features[3] <= 0.01314f) {
                            return 0; /* Benign (0) */
                        } else {
                            return 0; /* Benign (0) */
                        }
                    }
                }
            } else {
                /* Condition: ack_count <= 13.50000 */
                if (features[1] <= 13.50000f) {
                    /* Condition: IAT <= 0.05122 */
                    if (features[3] <= 0.05122f) {
                        return 1; /* Attack (1) */
                    } else {
                        return 0; /* Benign (0) */
                    }
                } else {
                    return 0; /* Benign (0) */
                }
            }
        }
    } else {
        /* Condition: Weight <= 29.50000 */
        if (features[0] <= 29.50000f) {
            /* Condition: ack_count <= 8.00000 */
            if (features[1] <= 8.00000f) {
                return 1; /* Attack (1) */
            } else {
                /* Condition: AVG <= 286.73059 */
                if (features[5] <= 286.73059f) {
                    return 0; /* Benign (0) */
                } else {
                    /* Condition: AVG <= 468.21338 */
                    if (features[5] <= 468.21338f) {
                        return 1; /* Attack (1) */
                    } else {
                        /* Condition: syn_count <= 0.50000 */
                        if (features[4] <= 0.50000f) {
                            return 0; /* Benign (0) */
                        } else {
                            return 0; /* Benign (0) */
                        }
                    }
                }
            }
        } else {
            /* Condition: Weight <= 32.50000 */
            if (features[0] <= 32.50000f) {
                /* Condition: ack_count <= 12.00000 */
                if (features[1] <= 12.00000f) {
                    return 1; /* Attack (1) */
                } else {
                    /* Condition: Tot size <= 8375.39087 */
                    if (features[7] <= 8375.39087f) {
                        return 0; /* Benign (0) */
                    } else {
                        /* Condition: AVG <= 390.61031 */
                        if (features[5] <= 390.61031f) {
                            return 1; /* Attack (1) */
                        } else {
                            return 0; /* Benign (0) */
                        }
                    }
                }
            } else {
                /* Condition: AVG <= 1124.24438 */
                if (features[5] <= 1124.24438f) {
                    /* Condition: ack_count <= 22.50000 */
                    if (features[1] <= 22.50000f) {
                        /* Condition: Weight <= 33.50000 */
                        if (features[0] <= 33.50000f) {
                            return 1; /* Attack (1) */
                        } else {
                            return 1; /* Attack (1) */
                        }
                    } else {
                        /* Condition: syn_count <= 1.50000 */
                        if (features[4] <= 1.50000f) {
                            return 0; /* Benign (0) */
                        } else {
                            return 1; /* Attack (1) */
                        }
                    }
                } else {
                    return 0; /* Benign (0) */
                }
            }
        }
    }
}
