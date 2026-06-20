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

package controllers

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	autoscalingv2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	hybaaiV1 "hyba-ai/k8s-operator/api/v1"
)

const (
	finalizerName = "ciaasservice.hyba.ai/finalizer"
)

// ComputationalIntelligenceServiceReconciler reconciles a ComputationalIntelligenceService object
type ComputationalIntelligenceServiceReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

//+kubebuilder:rbac:groups=hyba.ai,resources=ciaasservices,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=hyba.ai,resources=ciaasservices/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=hyba.ai,resources=ciaasservices/finalizers,verbs=update
//+kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=core,resources=services,verbs=get;list;watch;create;update;patch;delete

func (r *ComputationalIntelligenceServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := ctrl.LoggerFrom(ctx)

	service := &hybaaiV1.ComputationalIntelligenceService{}
	if err := r.Get(ctx, req.NamespacedName, service); err != nil {
		if apierrors.IsNotFound(err) {
			log.Info("Service resource not found. Ignoring since object must be deleted")
			return ctrl.Result{}, nil
		}
		log.Error(err, "Failed to get service")
		return ctrl.Result{}, err
	}

	// Check if service is being deleted
	if service.ObjectMeta.DeletionTimestamp != nil {
		if controllerutil.ContainsFinalizer(service, finalizerName) {
			if err := r.deleteExternalResources(ctx, service); err != nil {
				return ctrl.Result{}, err
			}
			controllerutil.RemoveFinalizer(service, finalizerName)
			if err := r.Update(ctx, service); err != nil {
				return ctrl.Result{}, err
			}
		}
		return ctrl.Result{}, nil
	}

	// Add finalizer
	if !controllerutil.ContainsFinalizer(service, finalizerName) {
		controllerutil.AddFinalizer(service, finalizerName)
		if err := r.Update(ctx, service); err != nil {
			return ctrl.Result{}, err
		}
	}

	// Create/Update Deployment
	deployment := &appsv1.Deployment{}
	deploymentName := service.Name + "-deployment"
	deploymentKey := types.NamespacedName{Name: deploymentName, Namespace: service.Namespace}

	if err := r.Get(ctx, deploymentKey, deployment); err != nil && apierrors.IsNotFound(err) {
		deployment = r.constructDeployment(service)
		log.Info("Creating new Deployment", "Deployment.Namespace", deployment.Namespace, "Deployment.Name", deployment.Name)
		if err := r.Create(ctx, deployment); err != nil {
			log.Error(err, "Failed to create new Deployment", "Deployment.Namespace", deployment.Namespace, "Deployment.Name", deployment.Name)
			return ctrl.Result{}, err
		}
	} else if err != nil {
		log.Error(err, "Failed to get Deployment")
		return ctrl.Result{}, err
	}

	// Create/Update Service
	svc := &corev1.Service{}
	svcKey := types.NamespacedName{Name: service.Name, Namespace: service.Namespace}
	if err := r.Get(ctx, svcKey, svc); err != nil && apierrors.IsNotFound(err) {
		svc = r.constructService(service)
		log.Info("Creating new Service", "Service.Namespace", svc.Namespace, "Service.Name", svc.Name)
		if err := r.Create(ctx, svc); err != nil {
			log.Error(err, "Failed to create new Service")
			return ctrl.Result{}, err
		}
	}

	// Create/Update HPA if scaling is enabled
	if service.Spec.Scaling != nil {
		hpa := &autoscalingv2.HorizontalPodAutoscaler{}
		hpaKey := types.NamespacedName{Name: service.Name + "-hpa", Namespace: service.Namespace}
		if err := r.Get(ctx, hpaKey, hpa); err != nil && apierrors.IsNotFound(err) {
			hpa = r.constructHPA(service)
			log.Info("Creating new HPA", "HPA.Namespace", hpa.Namespace, "HPA.Name", hpa.Name)
			if err := r.Create(ctx, hpa); err != nil {
				log.Error(err, "Failed to create new HPA")
				return ctrl.Result{}, err
			}
		}
	}

	// Update service status
	service.Status.State = "Running"
	service.Status.Ready = true
	service.Status.Message = "Service is operational"
	service.Status.LastUpdateTime = metav1.Now()

	// Set condition
	condition := metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionTrue,
		ObservedGeneration: service.Generation,
		Reason:             "ServiceReady",
		Message:            "Service is ready",
	}
	meta.SetStatusCondition(&service.Status.Conditions, condition)

	if err := r.Status().Update(ctx, service); err != nil {
		log.Error(err, "Failed to update service status")
		return ctrl.Result{}, err
	}

	return ctrl.Result{RequeueAfter: ctrl.Result{}.RequeueAfter}, nil
}

func (r *ComputationalIntelligenceServiceReconciler) constructDeployment(service *hybaaiV1.ComputationalIntelligenceService) *appsv1.Deployment {
	replicas := int32(1)
	if service.Spec.Scaling != nil && service.Spec.Scaling.MinReplicas > 0 {
		replicas = service.Spec.Scaling.MinReplicas
	}

	labels := map[string]string{
		"app":       service.Name,
		"component": "ciaas-service",
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      service.Name + "-deployment",
			Namespace: service.Namespace,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "service",
							Image: "hyba/ciaas-service:latest",
							Ports: []corev1.ContainerPort{
								{
									Name:          "http",
									ContainerPort: 8080,
									Protocol:      corev1.ProtocolTCP,
								},
							},
							Env: []corev1.EnvVar{
								{
									Name:  "SERVICE_NAME",
									Value: service.Name,
								},
								{
									Name:  "SERVICE_TIER",
									Value: service.Spec.Tier,
								},
								{
									Name:  "CONNECTOR_TYPE",
									Value: service.Spec.Connector.Type,
								},
							},
							Resources: corev1.ResourceRequirements{
								Requests: corev1.ResourceList{
									corev1.ResourceCPU:    *parseResourceQuantity("100m"),
									corev1.ResourceMemory: *parseResourceQuantity("256Mi"),
								},
								Limits: corev1.ResourceList{
									corev1.ResourceCPU:    *parseResourceQuantity("500m"),
									corev1.ResourceMemory: *parseResourceQuantity("512Mi"),
								},
							},
							LivenessProbe: &corev1.Probe{
								ProbeHandler: corev1.ProbeHandler{
									HTTPGet: &corev1.HTTPGetAction{
										Path: "/health",
										Port: intstr.FromInt(8080),
									},
								},
								InitialDelaySeconds: 10,
								PeriodSeconds:       10,
							},
							ReadinessProbe: &corev1.Probe{
								ProbeHandler: corev1.ProbeHandler{
									HTTPGet: &corev1.HTTPGetAction{
										Path: "/ready",
										Port: intstr.FromInt(8080),
									},
								},
								InitialDelaySeconds: 5,
								PeriodSeconds:       5,
							},
						},
					},
				},
			},
		},
	}

	controllerutil.SetControllerReference(service, deployment, r.Scheme)
	return deployment
}

func (r *ComputationalIntelligenceServiceReconciler) constructService(service *hybaaiV1.ComputationalIntelligenceService) *corev1.Service {
	labels := map[string]string{
		"app":       service.Name,
		"component": "ciaas-service",
	}

	svc := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      service.Name,
			Namespace: service.Namespace,
			Labels:    labels,
		},
		Spec: corev1.ServiceSpec{
			Selector: labels,
			Ports: []corev1.ServicePort{
				{
					Name:       "http",
					Port:       80,
					TargetPort: intstr.FromInt(8080),
					Protocol:   corev1.ProtocolTCP,
				},
			},
			Type: corev1.ServiceTypeClusterIP,
		},
	}

	controllerutil.SetControllerReference(service, svc, r.Scheme)
	return svc
}

func (r *ComputationalIntelligenceServiceReconciler) constructHPA(service *hybaaiV1.ComputationalIntelligenceService) *autoscalingv2.HorizontalPodAutoscaler {
	scaling := service.Spec.Scaling
	cpuTarget := int32(70)
	if scaling.TargetCPU > 0 {
		cpuTarget = scaling.TargetCPU
	}

	hpa := &autoscalingv2.HorizontalPodAutoscaler{
		ObjectMeta: metav1.ObjectMeta{
			Name:      service.Name + "-hpa",
			Namespace: service.Namespace,
		},
		Spec: autoscalingv2.HorizontalPodAutoscalerSpec{
			ScaleTargetRef: autoscalingv2.CrossVersionObjectReference{
				APIVersion: "apps/v1",
				Kind:       "Deployment",
				Name:       service.Name + "-deployment",
			},
			MinReplicas: &scaling.MinReplicas,
			MaxReplicas: scaling.MaxReplicas,
			Metrics: []autoscalingv2.MetricSpec{
				{
					Type: autoscalingv2.ResourceMetricSourceType,
					Resource: &autoscalingv2.ResourceMetricSource{
						Name: corev1.ResourceCPU,
						Target: autoscalingv2.MetricTarget{
							Type:               autoscalingv2.UtilizationMetricType,
							AverageUtilization: &cpuTarget,
						},
					},
				},
			},
		},
	}

	controllerutil.SetControllerReference(service, hpa, r.Scheme)
	return hpa
}

func (r *ComputationalIntelligenceServiceReconciler) deleteExternalResources(ctx context.Context, service *hybaaiV1.ComputationalIntelligenceService) error {
	// Delete associated Deployment
	deployment := &appsv1.Deployment{}
	deploymentKey := types.NamespacedName{Name: service.Name + "-deployment", Namespace: service.Namespace}
	if err := r.Get(ctx, deploymentKey, deployment); err == nil {
		if err := r.Delete(ctx, deployment); err != nil {
			return err
		}
	}

	// Delete associated Service
	svc := &corev1.Service{}
	svcKey := types.NamespacedName{Name: service.Name, Namespace: service.Namespace}
	if err := r.Get(ctx, svcKey, svc); err == nil {
		if err := r.Delete(ctx, svc); err != nil {
			return err
		}
	}

	return nil
}

func (r *ComputationalIntelligenceServiceReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&hybaaiV1.ComputationalIntelligenceService{}).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		Owns(&autoscalingv2.HorizontalPodAutoscaler{}).
		WithEventFilter(predicate.GenerationChangedPredicate{}).
		Complete(r)
}

func parseResourceQuantity(str string) *resource.Quantity {
	q, _ := resource.ParseQuantity(str)
	return &q
}
