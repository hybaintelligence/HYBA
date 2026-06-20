package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type Client struct {
	Endpoint string
	ApiKey   string
	HTTPClient *http.Client
}

func NewClient(endpoint, apiKey string) *Client {
	return &Client{
		Endpoint:   endpoint,
		ApiKey:     apiKey,
		HTTPClient: &http.Client{},
	}
}

// Service models
type Service struct {
	ID                string                 `json:"service_id"`
	Name              string                 `json:"name"`
	Tier              string                 `json:"service_tier"`
	State             string                 `json:"state"`
	Tenancy           string                 `json:"tenancy"`
	Owner             string                 `json:"owner"`
	CreatedAt         string                 `json:"created_at"`
	UpdatedAt         string                 `json:"updated_at"`
	CommercialPolicy  map[string]interface{} `json:"commercial_policy"`
	FaultTolerance    map[string]interface{} `json:"fault_tolerance"`
	Substrate         map[string]interface{} `json:"substrate"`
	EvidenceSeal      string                 `json:"evidence_seal"`
	ClaimBoundary     string                 `json:"claim_boundary"`
	Usage             map[string]interface{} `json:"usage"`
}

type ConnectorConfig struct {
	Type     string                 `json:"type"`
	Config   map[string]interface{} `json:"config"`
}

type OutputConfig struct {
	Type   string                 `json:"type"`
	Config map[string]interface{} `json:"config"`
}

// API methods
func (c *Client) CreateService(ctx context.Context, name, tier string, connector *ConnectorConfig) (*Service, error) {
	payload := map[string]interface{}{
		"name":           name,
		"service_tier":   tier,
		"connector":      connector,
	}

	return c.makeRequest(ctx, "POST", "/api/v1/computational-intelligence-services", payload)
}

func (c *Client) GetService(ctx context.Context, serviceID string) (*Service, error) {
	url := fmt.Sprintf("/api/v1/computational-intelligence-services/%s", serviceID)
	return c.makeRequest(ctx, "GET", url, nil)
}

func (c *Client) UpdateService(ctx context.Context, serviceID, name, tier string) (*Service, error) {
	payload := map[string]interface{}{
		"name":         name,
		"service_tier": tier,
	}

	url := fmt.Sprintf("/api/v1/computational-intelligence-services/%s", serviceID)
	return c.makeRequest(ctx, "PUT", url, payload)
}

func (c *Client) DeleteService(ctx context.Context, serviceID string) error {
	url := fmt.Sprintf("/api/v1/computational-intelligence-services/%s", serviceID)
	_, err := c.makeRequest(ctx, "DELETE", url, nil)
	return err
}

func (c *Client) ListServices(ctx context.Context) ([]*Service, error) {
	resp, err := c.doRequest(ctx, "GET", "/api/v1/computational-intelligence-services", nil)
	if err != nil {
		return nil, err
	}

	var services []*Service
	err = json.Unmarshal(resp, &services)
	if err != nil {
		return nil, err
	}

	return services, nil
}

func (c *Client) ListConnectors(ctx context.Context) (map[string]interface{}, error) {
	resp, err := c.doRequest(ctx, "GET", "/api/v1/connectors", nil)
	if err != nil {
		return nil, err
	}

	var connectors map[string]interface{}
	err = json.Unmarshal(resp, &connectors)
	if err != nil {
		return nil, err
	}

	return connectors, nil
}

// Helper methods
func (c *Client) makeRequest(ctx context.Context, method, path string, payload interface{}) (*Service, error) {
	resp, err := c.doRequest(ctx, method, path, payload)
	if err != nil {
		return nil, err
	}

	var service *Service
	err = json.Unmarshal(resp, &service)
	if err != nil {
		return nil, err
	}

	return service, nil
}

func (c *Client) doRequest(ctx context.Context, method, path string, payload interface{}) ([]byte, error) {
	url := fmt.Sprintf("%s%s", c.Endpoint, path)

	var body io.Reader
	if payload != nil {
		data, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}
		body = bytes.NewReader(data)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", c.ApiKey)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("API error: %d - %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}
