import requests
from collections import defaultdict

class FetchPools:
    def fetch_draftgroups(self):
        url = "https://www.draftkings.com/lobby/getcontests?sport=NFL"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            draftgroups = [
                {'DraftGroupId': group.get("DraftGroupId"), 'StartDateEst': group.get("StartDateEst")}
                for group in data.get("DraftGroups", [])
            ]
            return draftgroups
        except requests.RequestException as e:
            print(f"Error fetching draft groups for tennis: {e}")
            return []

    def fetch_draftables(self, draftgroup_id):
        url = f"https://api.draftkings.com/draftgroups/v1/draftgroups/{draftgroup_id}/draftables"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            draftables = [
                {
                    'DraftGroupId': draftgroup_id,
                    'displayName': draftable.get('displayName'),
                    'position': draftable.get('position'),
                    'salary': draftable.get('salary'),
                    'competition': draftable.get('competition', {}).get('name'),
                    'teamAbbreviation': draftable.get('teamAbbreviation'),
                }
                for draftable in data.get("draftables", [])
            ]
            return draftables
        except requests.RequestException as e:
            print(f"Error fetching draftables for DraftGroupId {draftgroup_id}: {e}")
            return []

    def organize_and_print_data(self, draft_groups, draftables):
        # Organize draft groups by StartDateEst
        groups_by_date = defaultdict(list)
        for group in draft_groups:
            start_date = group['StartDateEst'].split("T")[0]
            groups_by_date[start_date].append(group['DraftGroupId'])

        print("Draft Groups:")
        for date, group_ids in sorted(groups_by_date.items()):
            print(f"{date}:")
            for group_id in group_ids:
                print(f"  - DraftGroupId: {group_id}")

        # Organize draftables under each DraftGroupId
        draftables_by_group = defaultdict(list)
        for draftable in draftables:
            draftables_by_group[draftable['DraftGroupId']].append(draftable)

        print("\nDraftables:")
        for group_id, draftable_list in draftables_by_group.items():
            print(f"Draftables for DraftGroupId {group_id}:")
            seen = set()
            for d in draftable_list:
                key = (d['displayName'], d['position'], d['teamAbbreviation'], d['competition'])
                if key not in seen:
                    seen.add(key)
                    print(f"  - {d['displayName']} ({d['position']}, {d['teamAbbreviation']}, {d['competition']})")

if __name__ == "__main__":
    fetcher = FetchPools()

    # Fetch draft groups
    draft_groups = fetcher.fetch_draftgroups()

    # Fetch draftables for all draft groups
    all_draftables = []
    for group in draft_groups:
        draftgroup_id = group['DraftGroupId']
        draftables = fetcher.fetch_draftables(draftgroup_id)
        all_draftables.extend(draftables)

    # Organize and print the data
    fetcher.organize_and_print_data(draft_groups, all_draftables)

