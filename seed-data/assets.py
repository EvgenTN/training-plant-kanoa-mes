'''
Seeds the KanoaMES asset tree for the training plant.

The seed data mirrors importfiles/assets.json. Assets are matched by path, so
running this script more than once only adds the assets that are missing.

Run in the Gateway Script Console (Jython) by pasting this file, or:

	execfile('/path/to/seed-data/assets.py')
'''

SEED_ASSETS = [
	{
		'assetName': 'Training Plant',
		'assetPath': 'Training Plant',
		'assetTypeName': 'site',
		'assetTypePath': 'enterprise\\site',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'Receiving',
		'assetPath': 'Training Plant\\Receiving',
		'assetTypeName': 'area',
		'assetTypePath': 'enterprise\\site\\area',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'Bulk Storage',
		'assetPath': 'Training Plant\\Bulk Storage',
		'assetTypeName': 'area',
		'assetTypePath': 'enterprise\\site\\area',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'TRUCK01',
		'assetPath': 'Training Plant\\Receiving\\TRUCK01',
		'assetTypeName': 'Storage Location',
		'assetTypePath': 'enterprise\\site\\area\\Storage Location',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'TRUCK02',
		'assetPath': 'Training Plant\\Receiving\\TRUCK02',
		'assetTypeName': 'Storage Location',
		'assetTypePath': 'enterprise\\site\\area\\Storage Location',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'TK101',
		'assetPath': 'Training Plant\\Bulk Storage\\TK101',
		'assetTypeName': 'Storage Location',
		'assetTypePath': 'enterprise\\site\\area\\Storage Location',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'TK102',
		'assetPath': 'Training Plant\\Bulk Storage\\TK102',
		'assetTypeName': 'Storage Location',
		'assetTypePath': 'enterprise\\site\\area\\Storage Location',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	},
	{
		'assetName': 'TK103',
		'assetPath': 'Training Plant\\Bulk Storage\\TK103',
		'assetTypeName': 'Storage Location',
		'assetTypePath': 'enterprise\\site\\area\\Storage Location',
		'timeZone': 'UTC',
		'sortOrder': None,
		'enabled': True,
		'oeeEnabled': False
	}
]
#################################################################################
def _normalizePath(path):
	return '\\'.join([section.strip() for section in str(path).split('\\')])
#################################################################################
def _pathKey(path):
	return _normalizePath(path).lower()
#################################################################################
def _rows(dataset):
	if dataset is None:
		return []
	return system.kanoa.utilities.convertDatasetToJSON(dataset) or []
#################################################################################
def _assetsByPath():
	assetIds = {}
	for row in _rows(system.kanoa.asset.getAssets({})):
		assetPath = row.get('assetPath')
		if assetPath:
			assetIds[_pathKey(assetPath)] = row['assetId']
	return assetIds
#################################################################################
def _assetTypes():
	byPath = {}
	byName = {}
	for row in _rows(system.kanoa.asset.getAssetTypes({})):
		assetTypePath = row.get('assetTypePath') or row.get('path')
		if assetTypePath:
			byPath[_pathKey(assetTypePath)] = row['assetTypeId']
		assetTypeName = row.get('assetTypeName')
		if assetTypeName and assetTypeName.lower() not in byName:
			byName[assetTypeName.lower()] = row['assetTypeId']
	return byPath, byName
#################################################################################
def _addAdminAssetRole(assetId, userId, log):
	try:
		roleId = system.kanoa.utilities.getFieldValue('roleId', system.kanoa.security.getRoles({'roleName': 'Administrator'}))
		if roleId is not None:
			system.kanoa.security.addUserAssetRole({'assetId': assetId, 'roleId': roleId, 'userId': userId}, userId)
	except Exception as e:
		log.warn("Could not link Administrator role to assetId %s: %s" % (assetId, e))
#################################################################################
def assets(userId=None):
	'''
		Adds any missing training plant assets to KanoaMES.

		Args:
			userId (int): Optional Kanoa user id. Defaults to the SYSTEM user.

		Returns:
			dict: {'passed': bool, 'message': str, 'added': list, 'skipped': list}
	'''
	log = system.util.getLogger('kanoaScripts.seed')

	if userId is None:
		userId = system.kanoa.security.getIDPUserId({'userName': 'SYSTEM'})
	if userId is None:
		return {'passed': False, 'message': 'Could not resolve the SYSTEM user', 'added': [], 'skipped': []}

	assetIds = _assetsByPath()
	assetTypeIdsByPath, assetTypeIdsByName = _assetTypes()

	added = []
	skipped = []

	try:
		for seedAsset in sorted(SEED_ASSETS, key=lambda item: len(item['assetPath'].split('\\'))):
			assetPath = _normalizePath(seedAsset['assetPath'])
			assetPathKey = _pathKey(assetPath)
			assetTypePath = _normalizePath(seedAsset['assetTypePath'])

			if assetPathKey in assetIds:
				skipped.append(assetPath)
				log.info("Asset already exists, skipping: %s" % assetPath)
				continue

			parentPath = '\\'.join(assetPath.split('\\')[:-1]) or None
			parentId = assetIds.get(_pathKey(parentPath)) if parentPath else None
			if parentPath and parentId is None:
				raise Exception("Parent asset does not exist: %s" % parentPath)

			assetTypeId = assetTypeIdsByPath.get(_pathKey(assetTypePath)) or assetTypeIdsByName.get(seedAsset['assetTypeName'].lower())
			if assetTypeId is None:
				raise Exception("Asset type does not exist: %s" % assetTypePath)

			assetInfo = {
				'assetName': seedAsset['assetName'],
				'parentId': parentId,
				'assetTypeId': assetTypeId,
				'assetGroupId': None,
				'timeZone': seedAsset.get('timeZone'),
				'sortOrder': seedAsset.get('sortOrder'),
				'enabled': seedAsset.get('enabled', True),
				'oeeEnabled': seedAsset.get('oeeEnabled', False),
				'processTypeId': None
			}

			log.info("Adding asset %s with %s" % (assetPath, assetInfo))
			assetId, message = system.kanoa.asset.addAsset(assetInfo, userId)
			if message:
				raise Exception("Failed to add %s: %s" % (assetPath, message))

			assetIds[assetPathKey] = assetId
			added.append(assetPath)

			if parentId is None:
				_addAdminAssetRole(assetId, userId, log)

		system.kanoa.asset.populateAssetHierarchy()
	except Exception as e:
		log.error("Failed to seed assets. Added: %s. Error: %s" % (added, e))
		return {'passed': False, 'message': str(e), 'added': added, 'skipped': skipped}

	log.info("Asset seed complete. Added: %s. Skipped: %s" % (added, skipped))
	return {
		'passed': True,
		'message': 'Added %s asset(s); skipped %s existing asset(s)' % (len(added), len(skipped)),
		'added': added,
		'skipped': skipped
	}
#################################################################################
def main():
	result = assets()
	print(result)
	return result

if __name__ == '__main__':
	main()
