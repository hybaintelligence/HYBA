package provider

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"hyba-ai/terraform-provider-hyba/internal/client"
)

var (
	_ resource.Resource              = &CiaasServiceResource{}
	_ resource.ResourceWithImportState = &CiaasServiceResource{}
)

func NewCiaasServiceResource() resource.Resource {
	return &CiaasServiceResource{}
}

type CiaasServiceResource struct {
	client *client.Client
}

type CiaasServiceResourceModel struct {
	ID               types.String `tfsdk:"id"`
	Name             types.String `tfsdk:"name"`
	Tier             types.String `tfsdk:"tier"`
	State            types.String `tfsdk:"state"`
	Tenancy          types.String `tfsdk:"tenancy"`
	CreatedAt        types.String `tfsdk:"created_at"`
	UpdatedAt        types.String `tfsdk:"updated_at"`
	ConnectorType    types.String `tfsdk:"connector_type"`
	ConnectorConfig  types.Map    `tfsdk:"connector_config"`
	OutputType       types.String `tfsdk:"output_type"`
	OutputConfig     types.Map    `tfsdk:"output_config"`
	Tags             types.Map    `tfsdk:"tags"`
}

func (r *CiaasServiceResource) Metadata(ctx context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_ciaas_service"
}

func (r *CiaasServiceResource) Schema(ctx context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		MarkdownDescription: "Manages a HYBA Computational Intelligence Service.",
		Attributes: map[string]schema.Attribute{
			"id": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Service ID",
			},
			"name": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "Service name",
			},
			"tier": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "Service tier (developer, production, sovereign)",
			},
			"state": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Current service state",
			},
			"tenancy": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Tenancy mode",
			},
			"created_at": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Creation timestamp",
			},
			"updated_at": schema.StringAttribute{
				Computed:            true,
				MarkdownDescription: "Last update timestamp",
			},
			"connector_type": schema.StringAttribute{
				Optional:            true,
				MarkdownDescription: "Connector type (sql_snowflake, kafka, s3, etc)",
			},
			"connector_config": schema.MapAttribute{
				ElementType:         types.StringType,
				Optional:            true,
				MarkdownDescription: "Connector configuration",
			},
			"output_type": schema.StringAttribute{
				Optional:            true,
				MarkdownDescription: "Output type",
			},
			"output_config": schema.MapAttribute{
				ElementType:         types.StringType,
				Optional:            true,
				MarkdownDescription: "Output configuration",
			},
			"tags": schema.MapAttribute{
				ElementType:         types.StringType,
				Optional:            true,
				MarkdownDescription: "Service tags",
			},
		},
	}
}

func (r *CiaasServiceResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}

	client, ok := req.ProviderData.(*client.Client)
	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected Resource Configure Type",
			fmt.Sprintf("Expected *client.Client, got: %T. Please report this issue to the provider developers.", req.ProviderData),
		)
		return
	}

	r.client = client
}

func (r *CiaasServiceResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	var data *CiaasServiceResourceModel

	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Build connector config
	var connectorConfig *client.ConnectorConfig
	if !data.ConnectorType.IsNull() {
		connectorConfig = &client.ConnectorConfig{
			Type: data.ConnectorType.ValueString(),
		}
	}

	// Create service
	service, err := r.client.CreateService(
		ctx,
		data.Name.ValueString(),
		data.Tier.ValueString(),
		connectorConfig,
	)
	if err != nil {
		resp.Diagnostics.AddError("Error creating service", err.Error())
		return
	}

	// Update model
	data.ID = types.StringValue(service.ID)
	data.State = types.StringValue(service.State)
	data.Tenancy = types.StringValue(service.Tenancy)
	data.CreatedAt = types.StringValue(service.CreatedAt)
	data.UpdatedAt = types.StringValue(service.UpdatedAt)

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

func (r *CiaasServiceResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var data *CiaasServiceResourceModel

	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	service, err := r.client.GetService(ctx, data.ID.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Error reading service", err.Error())
		return
	}

	data.State = types.StringValue(service.State)
	data.UpdatedAt = types.StringValue(service.UpdatedAt)

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

func (r *CiaasServiceResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	var data *CiaasServiceResourceModel

	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	service, err := r.client.UpdateService(
		ctx,
		data.ID.ValueString(),
		data.Name.ValueString(),
		data.Tier.ValueString(),
	)
	if err != nil {
		resp.Diagnostics.AddError("Error updating service", err.Error())
		return
	}

	data.UpdatedAt = types.StringValue(service.UpdatedAt)

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

func (r *CiaasServiceResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var data *CiaasServiceResourceModel

	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	err := r.client.DeleteService(ctx, data.ID.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Error deleting service", err.Error())
		return
	}
}

func (r *CiaasServiceResource) ImportState(ctx context.Context, req resource.ImportStateRequest, resp *resource.ImportStateResponse) {
	service, err := r.client.GetService(ctx, req.ID)
	if err != nil {
		resp.Diagnostics.AddError("Error importing service", err.Error())
		return
	}

	data := &CiaasServiceResourceModel{
		ID:        types.StringValue(service.ID),
		Name:      types.StringValue(service.Name),
		Tier:      types.StringValue(service.Tier),
		State:     types.StringValue(service.State),
		Tenancy:   types.StringValue(service.Tenancy),
		CreatedAt: types.StringValue(service.CreatedAt),
		UpdatedAt: types.StringValue(service.UpdatedAt),
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}
