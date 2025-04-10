def patch_sw360_for_batch_update():
    from sw360 import SW360
    import requests

    def update_project_release_relationships_batch(self, project_id: str, relationships: list[dict]) -> bool:
        url = f"{self.url}/resource/api/projects/{project_id}/releases"
        body = {"releases": relationships}

        response = self.session.put(url, json=body)

        if response.status_code in [200, 204]:
            print("✅ Batch release relationship update successful.")
            return True
        else:
            print(f"❌ Failed to batch update: {response.status_code} - {response.text}")
            return False

    SW360.update_project_release_relationships_batch = update_project_release_relationships_batch
