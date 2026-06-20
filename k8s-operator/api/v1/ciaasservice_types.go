/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ComputationalIntelligenceServiceSpec defines the desired state
type ComputationalIntelligenceServiceSpec struct {
	Name            string                  `json:"name"`
	Tier            string                  `json:"tier"`
	Connector       ConnectorSpec           `json:"connector,omitempty"`
	Output          OutputSpec              `json:"output,omitempty"`
	Scaling         *ScalingSpec            `json:"scaling,omitempty"`
	Monitoring      *MonitoringSpec         `json:"monitoring,omitempty"`
	PoliciesEnabled bool                    `json:"policiesEnabled,omitempty"`
}

type ConnectorSpec struct {
	Type   string                 `json:"type"`
	Config map[string]interface{} `json:"config,omitempty"`
}

type OutputSpec struct {
	Type   string                 `json:"type"`
	Config map[string]interface{} `json:"config,omitempty"`
}

type ScalingSpec struct {
	MinReplicas int32 `json:"minReplicas,omitempty"`
	MaxReplicas int32 `json:"maxReplicas,omitempty"`
	TargetCPU   int32 `json:"targetCPU,omitempty"`
}

type MonitoringSpec struct {
	Enabled             bool   `json:"enabled,omitempty"`
	DatadogIntegration  bool   `json:"datadogIntegration,omitempty"`
	PrometheusInterval  string `json:"prometheusInterval,omitempty"`
	LogLevel            string `json:"logLevel,omitempty"`
}

// ComputationalIntelligenceServiceStatus defines the observed state
type ComputationalIntelligenceServiceStatus struct {
	State              string      `json:"state,omitempty"`
	Ready              bool        `json:"ready"`
	Replicas           int32       `json:"replicas"`
	UpdatedReplicas    int32       `json:"updatedReplicas"`
	AvailableReplicas  int32       `json:"availableReplicas"`
	LastUpdateTime     metav1.Time `json:"lastUpdateTime,omitempty"`
	LastTransitionTime metav1.Time `json:"lastTransitionTime,omitempty"`
	Message            string      `json:"message,omitempty"`
	Conditions         []Condition `json:"conditions,omitempty"`
}

type Condition struct {
	Type               string      `json:"type"`
	Status             string      `json:"status"`
	Reason             string      `json:"reason,omitempty"`
	Message            string      `json:"message,omitempty"`
	LastTransitionTime metav1.Time `json:"lastTransitionTime,omitempty"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status
//+kubebuilder:resource:shortName=ciaas;ciaases

// ComputationalIntelligenceService is the Schema for computational intelligence services
type ComputationalIntelligenceService struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ComputationalIntelligenceServiceSpec   `json:"spec,omitempty"`
	Status ComputationalIntelligenceServiceStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// ComputationalIntelligenceServiceList contains a list of ComputationalIntelligenceService
type ComputationalIntelligenceServiceList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ComputationalIntelligenceService `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ComputationalIntelligenceService{}, &ComputationalIntelligenceServiceList{})
}

// SetupWebhookWithManager registers the webhook with the manager
func (r *ComputationalIntelligenceService) SetupWebhookWithManager(mgr interface{}) error {
	// Webhook implementation would go here
	// For now, this is a placeholder
	return nil
}
