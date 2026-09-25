// OPTIONAL: Neo4j Labs Aura Terraform provider.
// This is intentionally separated from the AWS module because the provider
// is a Neo4j Labs project and its current resource schema can evolve.
//
// Official reference:
// https://neo4j.com/labs/neo4j-aura-terraform-provider/
//
// terraform {
//   required_providers {
//     neo4jaura = {
//       source  = "neo4j-labs/neo4jaura"
//       version = "0.0.1-beta"
//     }
//   }
// }
//
// provider "neo4jaura" {}
//
// Configure AURA credentials through environment variables or your approved
// secret mechanism. Do not commit client IDs or secrets.
//
// Use the provider's current examples to add the AuraDB instance resource.
// The importer is intentionally decoupled from provisioning so a user can
// also target an existing AuraDB instance.
