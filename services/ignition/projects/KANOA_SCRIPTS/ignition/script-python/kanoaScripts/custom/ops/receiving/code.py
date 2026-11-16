import threading


_orderLocks = {}
_orderLocksGuard = threading.Lock()
_receivingSerialName = None


def getLogger():
	"""Return the named logger used by the receiving workflow.

	Args:
		None
	Returns:
		Logger: Ignition logger for receiving operations.
	Updated:
		2026-11-13: Initial implementation.
	"""
	return system.util.getLogger('kanoaScripts.receiving')


def _acquireResourceLock(resourceKey):
	"""Acquire the process-wide receiving lock for a serialized resource key.

	Args:
		resourceKey (str): Stable key for one order or lot operation.
	Returns:
		Lock: Reentrant lock scoped to this Gateway script module.
	Updated:
		2026-11-13: Initial implementation.
	"""
	key = str(resourceKey)
	_orderLocksGuard.acquire()
	try:
		lock = _orderLocks.get(key)
		if lock is None:
			lock = threading.RLock()
			_orderLocks[key] = lock
	finally:
		_orderLocksGuard.release()
	lock.acquire()
	return lock


def _acquireOrderLock(workOrderId):
	"""Acquire the process-wide receiving lock for one order ID.

	Args:
		workOrderId (int): Stable Kanoa production order identifier.
	Returns:
		Lock: Reentrant lock scoped to this Gateway script module.
	Updated:
		2026-11-13: Initial implementation.
	"""
	return _acquireResourceLock('order:%s' % int(workOrderId))


def _releaseResourceLock(lock):
	"""Release a lock acquired by _acquireResourceLock.

	Args:
		lock (Lock): Lock returned by a receiving lock helper.
	Returns:
		None
	Updated:
		2026-11-13: Initial implementation.
	"""
	lock.release()


def makeResult(status, message, data=None):
	"""Build the serializable result shape shared with Perspective views.

	Args:
		status (str): Contract status such as SUCCESS or VALIDATION_ERROR.
		message (str): Operator-safe outcome or next action.
		data (dict): Optional display and recovery fields.
	Returns:
		dict: JSON-compatible status, message, and data values.
	Updated:
		2026-11-13: Initial implementation.
	"""
	return {
		'status': status,
		'message': message or '',
		'data': data or {}
	}


def getAuthenticatedUserId(authUser):
	"""Resolve the authenticated Perspective user to a Kanoa user ID.

	Args:
		authUser (dict): Perspective session.props.auth.user value.
	Returns:
		int: Kanoa user ID for the authenticated user.
	Raises:
		ValueError: If no authenticated user or Kanoa ID is available.
	Updated:
		2026-11-13: Initial implementation.
	"""
	if not authUser or not authUser.get('userName'):
		raise ValueError('An authenticated Perspective user is required.')

	userId = system.kanoa.security.getIDPUserId(authUser)
	if userId is None:
		raise ValueError('The authenticated user is not configured in Kanoa.')
	return userId


def getReceivingConfiguration(serialName=None):
	"""Resolve required operation and lot configuration by configured names.

	Args:
		serialName (str): Optional configured Kanoa serial definition name. When
			omitted, exactly one enabled serial definition must exist.
	Returns:
		dict: Shared result containing resolved Kanoa IDs or an actionable error.
	Updated:
		2026-11-13: Initial implementation.
	"""
	if not serialName:
		try:
			serialRows = _datasetRows(system.kanoa.serial.getSerialNumbers({}))
			serialRows = [row for row in serialRows if row.get('enabled', True)]
		except Exception as exc:
			getLogger().error('getReceivingConfiguration() serial lookup failed: %s' % str(exc))
			return makeResult('CONFIGURATION_ERROR', 'Could not load Kanoa serial definitions.')
		if len(serialRows) != 1:
			return makeResult(
				'CONFIGURATION_ERROR',
				'Configure one receiving serial definition or set its name in the receiving script configuration.'
			)
		serialName = serialRows[0].get('serialName')
		if not serialName:
			return makeResult('CONFIGURATION_ERROR', 'The configured Kanoa serial definition has no name.')

	lookups = [
		('receiveOperationId', 'Receive operation', system.kanoa.lot.getLotOperations,
			{'lotOperationName': 'Receive', 'enabled': True}, 'lotOperationId'),
		('transferOperationId', 'Transfer operation', system.kanoa.lot.getLotOperations,
			{'lotOperationName': 'Transfer', 'enabled': True}, 'lotOperationId'),
		('initialLotStateId', 'OK lot state', system.kanoa.lot.getLotStates,
			{'lotStateName': 'OK', 'enabled': True}, 'lotStateId'),
		('inputSourceId', 'input item source', system.kanoa.item.getItemSource,
			{'itemSourceName': 'input', 'enabled': True}, 'itemSourceId'),
		('outputSourceId', 'output item source', system.kanoa.item.getItemSource,
			{'itemSourceName': 'output', 'enabled': True}, 'itemSourceId'),
		('kgUnitId', 'kg item unit', system.kanoa.item.getItemUnits,
			{'itemUnitName': 'kg', 'enabled': True}, 'itemUnitId'),
		('serialId', 'configured serial definition', system.kanoa.serial.getSerialNumbers,
			{'serialName': serialName}, 'serialId')
	]

	configuration = {}
	missing = []
	for resultKey, displayName, lookupFunction, params, idField in lookups:
		try:
			value = system.kanoa.utilities.getFieldValue(idField, lookupFunction(params))
		except Exception as exc:
			getLogger().error(
				'getReceivingConfiguration() failed looking up %s: %s' %
				(displayName, str(exc))
			)
			return makeResult(
				'CONFIGURATION_ERROR',
				'Could not verify the %s in Kanoa. Ask a Kanoa administrator to check the receiving configuration.' % displayName
			)

		if value is None:
			missing.append(displayName)
		else:
			configuration[resultKey] = value

	if missing:
		getLogger().warn(
			'Receiving configuration is incomplete; missing: %s' % ', '.join(missing)
		)
		return makeResult(
			'CONFIGURATION_ERROR',
			'Receiving is not configured in Kanoa. Missing: %s.' % ', '.join(missing)
		)

	configuration['serialName'] = serialName
	return makeResult('SUCCESS', 'Receiving configuration loaded.', configuration)


def _getTransferConfiguration():
	"""Resolve only the configuration required to move an existing lot.

	Args:
		None
	Returns:
		dict: Shared result containing Transfer and item-source IDs.
	Updated:
		2026-11-13: Initial implementation.
	"""
	lookups = [
		('transferOperationId', 'Transfer operation', system.kanoa.lot.getLotOperations,
			{'lotOperationName': 'Transfer', 'enabled': True}, 'lotOperationId'),
		('inputSourceId', 'input item source', system.kanoa.item.getItemSource,
			{'itemSourceName': 'input', 'enabled': True}, 'itemSourceId'),
		('outputSourceId', 'output item source', system.kanoa.item.getItemSource,
			{'itemSourceName': 'output', 'enabled': True}, 'itemSourceId')
	]
	configuration = {}
	missing = []
	for resultKey, displayName, lookupFunction, params, idField in lookups:
		try:
			value = system.kanoa.utilities.getFieldValue(idField, lookupFunction(params))
		except Exception as exc:
			getLogger().error('_getTransferConfiguration() lookup failed for %s: %s' % (displayName, str(exc)))
			return makeResult('CONFIGURATION_ERROR', 'Could not verify the %s in Kanoa.' % displayName)
		if value is None:
			missing.append(displayName)
		else:
			configuration[resultKey] = value
	if missing:
		return makeResult('CONFIGURATION_ERROR', 'Transfer recovery is not configured. Missing: %s.' % ', '.join(missing))
	return makeResult('SUCCESS', 'Transfer configuration loaded.', configuration)


def _datasetRows(dataset):
	"""Convert a Kanoa dataset or row list to serializable dictionaries.

	Args:
		dataset: Dataset or iterable returned by a Kanoa system function.
	Returns:
		list: Rows converted by the documented Kanoa utility.
	Updated:
		2026-11-13: Initial implementation.
	"""
	if dataset is None:
		return []
	if hasattr(dataset, 'rowCount'):
		if dataset.rowCount == 0:
			return []
		return system.kanoa.utilities.convertDatasetToJSON(dataset)
	if isinstance(dataset, dict):
		return [dataset]
	return list(dataset)


def _getOrder(workOrderId):
	"""Load the canonical Kanoa production order row.

	Args:
		workOrderId (int): Stable Kanoa production order identifier.
	Returns:
		dict or None: Canonical order row, or None when it no longer exists.
	Updated:
		2026-11-13: Initial implementation.
	"""
	try:
		workOrderId = int(workOrderId)
	except (TypeError, ValueError):
		return None

	rows = _datasetRows(system.kanoa.order.getProductionOrders({
		'workOrderId': workOrderId,
		'ignoreActualQty': True
	}))
	return rows[0] if rows else None


def _orderSummary(order):
	"""Shape a production order into operator-safe display fields.

	Args:
		order (dict): Canonical Kanoa production order row.
	Returns:
		dict: Minimal order summary; no editable schedule values are included.
	Updated:
		2026-11-13: Initial implementation.
	"""
	description = order.get('workOrderTitle') or order.get('itemDescription') or ''
	return {
		'workOrderId': order.get('workOrderId'),
		'orderNumber': order.get('workOrderName'),
		'description': description,
		'material': order.get('itemName'),
		'itemId': order.get('itemId'),
		'targetQty': order.get('reqdQty'),
		'unitName': order.get('itemUnitName'),
		'itemUnitId': order.get('itemUnitId'),
		'status': order.get('workOrderStatusName')
	}


def getScheduledReceivingOrders(startDate, endDate):
	"""Return eligible production orders scheduled in a date window.

	Args:
		startDate (Date): Inclusive schedule window start.
		endDate (Date): Inclusive schedule window end.
	Returns:
		dict: Shared result with shaped schedule entries or an error.
	Updated:
		2026-11-13: Initial implementation.
	"""
	if startDate is None or endDate is None or system.date.isAfter(startDate, endDate):
		return makeResult('VALIDATION_ERROR', 'Choose a valid receiving schedule date range.')

	try:
		# Prefer expanded calendar events. If this environment has no saved
		# operation blocks, fall back to eligible production orders by due date.
		calendarStart = system.date.addDays(startDate, -1)
		calendarEnd = system.date.addDays(endDate, 1)
		events = _datasetRows(system.kanoa.schedule.getCalendarEvents({
			'scheduleType': 'operation',
			'startDate': calendarStart,
			'endDate': calendarEnd,
			'assetPath': '%'
		}))
		if not events:
			events = _datasetRows(system.kanoa.schedule.getScheduleBlocks({
				'startDate': calendarStart,
				'endDate': calendarEnd
			}))
		if not events:
			statusOrders = _datasetRows(system.kanoa.order.getProductionOrders({
				'workOrderStatusList': ['Scheduled', 'In Progress'],
				'ignoreActualQty': False
			}))
			for order in statusOrders:
				dueDate = order.get('dueDate')
				if dueDate is None or system.date.isBefore(dueDate, startDate) or system.date.isAfter(dueDate, endDate):
					continue
				events.append({
					'workOrderId': order.get('workOrderId'),
					'scheduleBlockId': None,
					'startDate': dueDate,
					'_canonicalOrder': order
				})
		orders = []
		seen = set()
		for event in events:
			workOrderId = event.get('workOrderId')
			if workOrderId is None:
				continue
			order = event.get('_canonicalOrder') or _getOrder(workOrderId)
			status = order.get('workOrderStatusName') if order else 'Missing order'
			if not order or status not in ('Scheduled', 'In Progress'):
				continue

			if workOrderId in seen:
				continue
			seen.add(workOrderId)

			entry = _orderSummary(order)
			entry.update({
				'scheduleBlockId': event.get('scheduleBlockId') or event.get('uuid'),
				'scheduledStart': event.get('startDate') or event.get('start'),
				'scheduledEnd': event.get('endDate') or event.get('end')
			})
			orders.append(entry)

		orders.sort(key=lambda row: (row.get('scheduledStart') is None, row.get('scheduledStart')))
		return makeResult('SUCCESS', 'Scheduled receiving orders loaded.', {'orders': orders})
	except Exception as exc:
		getLogger().error('getScheduledReceivingOrders() failed: %s' % str(exc))
		return makeResult(
			'ERROR',
			'Could not load the receiving schedule. Refresh the screen or contact a supervisor.'
		)


def getReceivingOrder(workOrderId):
	"""Reload canonical order data and confirm it is eligible for receiving.

	Args:
		workOrderId (int): Stable Kanoa production order identifier.
	Returns:
		dict: Shared result with canonical read-only order fields.
	Updated:
		2026-11-13: Initial implementation.
	"""
	order = _getOrder(workOrderId)
	if not order:
		return makeResult('NOT_ELIGIBLE', 'This receiving order no longer exists. Refresh the schedule.')
	if order.get('workOrderStatusName') not in ('Scheduled', 'In Progress'):
		return makeResult('NOT_ELIGIBLE', 'This order is no longer eligible for receiving.')

	orderSummary = _orderSummary(order)
	return makeResult('SUCCESS', 'Receiving order loaded.', {'order': orderSummary})


def getReceivingAssets():
	"""Return enabled Storage Locations scoped to receiving trucks and tanks.

	Args:
		None
	Returns:
		dict: Shared result with separate truck and destination lists.
	Updated:
		2026-11-13: Initial implementation.
	"""
	try:
		trucks = _datasetRows(system.kanoa.asset.getAssets({
			'assetPath': 'Training Plant\\Receiving\\%',
			'assetTypeName': 'Storage Location',
			'enabled': True
		}))
		tanks = _datasetRows(system.kanoa.asset.getAssets({
			'assetPath': 'Training Plant\\Bulk Storage\\%',
			'assetTypeName': 'Storage Location',
			'enabled': True
		}))
		shape = lambda asset: {
			'assetId': asset.get('assetId'),
			'assetName': asset.get('assetName'),
			'assetPath': asset.get('assetPath')
		}
		return makeResult('SUCCESS', 'Receiving assets loaded.', {
			'trucks': [shape(asset) for asset in trucks],
			'tanks': [shape(asset) for asset in tanks]
		})
	except Exception as exc:
		getLogger().error('getReceivingAssets() failed: %s' % str(exc))
		return makeResult(
			'ERROR',
			'Could not load receiving assets. Refresh the screen or contact a supervisor.'
		)


def getReceivedQtyForOrder(workOrderId):
	"""Sum enabled Receive output events for an order, requiring comparable kg.

	Args:
		workOrderId (int): Stable Kanoa production order identifier.
	Returns:
		dict: Shared result with cumulative received quantity in kg.
	Updated:
		2026-11-13: Initial implementation.
	"""
	from decimal import Decimal, InvalidOperation

	order = _getOrder(workOrderId)
	if not order:
		return makeResult('NOT_ELIGIBLE', 'This receiving order no longer exists. Refresh the schedule.')
	if (order.get('itemUnitName') or '').strip().lower() != 'kg':
		return makeResult(
			'UNIT_ERROR',
			'This order is not in kg. Receiving is blocked until its unit conversion is verified.'
		)

	kgUnitId = system.kanoa.utilities.getFieldValue(
		'itemUnitId', system.kanoa.item.getItemUnits({'itemUnitName': 'kg', 'enabled': True})
	)
	if kgUnitId is None:
		return makeResult('CONFIGURATION_ERROR', 'The enabled kg item unit is missing in Kanoa.')

	try:
		events = _datasetRows(system.kanoa.lot.getLotEvents({
			'workOrderId': int(workOrderId),
			'lotOperationName': 'Receive',
			'itemSourceName': 'output',
			'enabled': True
		}))
		totalQty = Decimal('0')
		for event in events:
			eventUnitId = event.get('itemUnitId')
			if eventUnitId is None or int(eventUnitId) != int(kgUnitId):
				return makeResult(
					'UNIT_ERROR',
					'Receipt history contains a unit other than kg or a missing unit. Ask a supervisor to reconcile the order.'
				)
			try:
				quantity = Decimal(str(event.get('lotEventQty')))
			except (TypeError, ValueError, InvalidOperation):
				return makeResult('DATA_ERROR', 'Receipt history contains an invalid quantity. Ask a supervisor to reconcile the order.')
			if not quantity.is_finite() or quantity < 0:
				return makeResult('DATA_ERROR', 'Receipt history contains an invalid quantity. Ask a supervisor to reconcile the order.')
			totalQty += quantity
		return makeResult('SUCCESS', 'Receipt history loaded.', {
			'receivedQtyKg': float(totalQty),
			'receivedQtyKgExact': str(totalQty),
			'receiptEventCount': len(events)
		})
	except Exception as exc:
		getLogger().error('getReceivedQtyForOrder() failed for workOrderId %s: %s' % (workOrderId, str(exc)))
		return makeResult(
			'ERROR',
			'Could not read receipt history. Do not retry a receipt until this order has been reconciled.'
		)


def _getEligibleAsset(assetId, basePath):
	"""Reload and validate an enabled Storage Location in an allowed area.

	Args:
		assetId (int): Selected Kanoa asset ID.
		basePath (str): Allowed area path ending at Receiving or Bulk Storage.
	Returns:
		dict or None: Current asset row when it is eligible.
	Updated:
		2026-11-13: Initial implementation.
	"""
	try:
		rows = _datasetRows(system.kanoa.asset.getAssets({
			'assetId': int(assetId),
			'enabled': True
		}))
	except Exception:
		return None
	if len(rows) != 1:
		return None
	asset = rows[0]
	path = asset.get('assetPath') or ''
	if asset.get('assetTypeName') != 'Storage Location':
		return None
	if not path.startswith(basePath + '\\'):
		return None
	return asset


def _getLotActivityAtAsset(lotId, assetId):
	"""Return the unique current positive inventory row for a lot at an asset.

	Args:
		lotId (int): Kanoa lot identifier.
		assetId (int): Kanoa asset identifier.
	Returns:
		dict or None: Current activity row when exactly one positive row exists.
	Updated:
		2026-11-13: Initial implementation.
	"""
	rows = _datasetRows(system.kanoa.lot.getLotActivity({
		'lotId': int(lotId),
		'assetId': int(assetId),
		'hasQty': True
	}))
	positiveRows = []
	for row in rows:
		try:
			qty = float(row.get('lotEventQty'))
		except (TypeError, ValueError):
			continue
		if qty > 0:
			positiveRows.append(row)
	return positiveRows[0] if len(positiveRows) == 1 else None


def _findLotId(lotName):
	"""Resolve a unique Kanoa lot ID from its serial-generated name.

	Args:
		lotName (str): Serial-generated Kanoa lot name.
	Returns:
		int or None: Lot ID when exactly one lot exists.
	Updated:
		2026-11-13: Initial implementation.
	"""
	rows = _datasetRows(system.kanoa.lot.getLots({'lotName': lotName, 'enabled': True}))
	return rows[0].get('lotId') if len(rows) == 1 else None


def checkReceiptAttempt(workOrderId, lotName):
	"""Reconcile an uncertain receipt by checking its generated lot name in Kanoa.

	Args:
		workOrderId (int): Associated Kanoa production order ID.
		lotName (str): Serial allocated for the attempted receipt.
	Returns:
		dict: SUCCESS with the recorded receipt, or RECONCILIATION_REQUIRED.
	Updated:
		2026-11-13: Initial implementation.
	"""
	if not lotName:
		return makeResult('RECONCILIATION_REQUIRED', 'Receipt identity is unavailable. Check order and lot history before submitting again.')
	try:
		rows = _datasetRows(system.kanoa.lot.getLotEvents({
			'workOrderId': int(workOrderId),
			'lotName': lotName,
			'lotOperationName': 'Receive',
			'itemSourceName': 'output',
			'enabled': True
		}))
	except Exception as exc:
		getLogger().error('checkReceiptAttempt() failed workOrderId=%s lotName=%s: %s' %
			(workOrderId, lotName, str(exc)))
		return makeResult('RECONCILIATION_REQUIRED', 'Receipt history could not be checked. Do not submit another receipt until an administrator reconciles this order.')

	if len(rows) != 1:
		return makeResult('RECONCILIATION_REQUIRED', 'The receipt result is not conclusive. Check order and lot history before submitting again.', {
			'workOrderId': int(workOrderId), 'lotName': lotName,
			'matchingReceiptEvents': len(rows)
		})
	event = rows[0]
	return makeResult('SUCCESS', 'The receipt is recorded in Kanoa.', {
		'workOrderId': int(workOrderId), 'lotName': lotName,
		'lotId': event.get('lotId'),
		'receiveOperationEventId': event.get('lotOperationEventId'),
		'receiveLotEventId': event.get('lotEventId'),
		'quantityKg': event.get('lotEventQty'),
		'assetId': event.get('assetId')
	})


def _performTransfer(lotId, truckAssetId, tankAssetId, qty, userId, configuration):
	"""Serialize and perform a transfer of an existing lot.

	Args:
		lotId (int): Existing Kanoa lot identifier.
		truckAssetId (int): Current Receiving Storage Location.
		tankAssetId (int): Destination Bulk Storage Storage Location.
		qty (float): Quantity to transfer in kg.
		userId (int): Authenticated Kanoa user ID.
		configuration (dict): Resolved operation and item-source IDs.
	Returns:
		dict: Shared transfer outcome.
	Updated:
		2026-11-13: Initial implementation.
	"""
	lock = _acquireResourceLock('lot:%s' % int(lotId))
	try:
		return _performTransferLocked(lotId, truckAssetId, tankAssetId, qty, userId, configuration)
	finally:
		_releaseResourceLock(lock)


def _performTransferLocked(lotId, truckAssetId, tankAssetId, qty, userId, configuration):
	"""Transfer current lot quantity from one validated asset to another.

	Args:
		lotId (int): Existing Kanoa lot identifier.
		truckAssetId (int): Current Receiving Storage Location.
		tankAssetId (int): Destination Bulk Storage Storage Location.
		qty (float): Quantity to transfer in kg.
		userId (int): Authenticated Kanoa user ID.
		configuration (dict): Resolved operation and item-source IDs.
	Returns:
		dict: Shared transfer outcome, including recovery state when pending.
	Updated:
		2026-11-13: Initial implementation.
	"""
	truck = _getEligibleAsset(truckAssetId, 'Training Plant\\Receiving')
	tank = _getEligibleAsset(tankAssetId, 'Training Plant\\Bulk Storage')
	if not truck or not tank:
		return makeResult('VALIDATION_ERROR', 'The selected truck or tank is no longer eligible. Refresh the asset lists.')

	activity = _getLotActivityAtAsset(lotId, truckAssetId)
	if not activity:
		return makeResult('NOT_ELIGIBLE', 'This lot no longer has a single positive quantity at the selected truck. Refresh pending transfers.')
	try:
		availableQty = float(activity.get('lotEventQty'))
		transferQty = float(qty)
	except (TypeError, ValueError):
		return makeResult('DATA_ERROR', 'The current lot quantity is invalid. Ask a supervisor to reconcile it.')
	if transferQty <= 0 or transferQty > availableQty:
		return makeResult('VALIDATION_ERROR', 'The lot no longer has enough quantity at this truck. Refresh pending transfers.')

	lotEventInfo = {
		'lotId': int(lotId),
		'lotName': activity.get('lotName'),
		'itemId': activity.get('itemId'),
		'itemUnitId': activity.get('itemUnitId'),
		'lotEventQty': transferQty,
		'workOrderId': activity.get('workOrderId'),
		'lotStateId': activity.get('lotStateId'),
		'lotStateReasonId': activity.get('lotStateReasonId'),
		'shiftId': None,
		'tStamp': system.date.now(),
		'comment': None,
		'lotOperationEventId': None,
		'assetTransportId': None
	}
	inputEvent = dict(lotEventInfo)
	inputEvent['assetId'] = int(truckAssetId)
	inputEvent['itemSourceId'] = configuration['inputSourceId']
	outputEvent = dict(lotEventInfo)
	outputEvent['assetId'] = int(tankAssetId)
	outputEvent['itemSourceId'] = configuration['outputSourceId']
	operationInfo = {
		'lotOperationEventId': None,
		'lotOperationId': configuration['transferOperationId'],
		'assetId': int(tankAssetId),
		'tStamp': system.date.now(),
		'enabled': True
	}

	getLogger().info(
		'Transfer start lotId=%s truckAssetId=%s tankAssetId=%s qtyKg=%s' %
		(lotId, truckAssetId, tankAssetId, transferQty)
	)
	try:
		operationEventId, message = system.kanoa.lot.executeLotOperation(
			operationInfo, [inputEvent], [outputEvent], userId
		)
	except Exception as exc:
		getLogger().error(
			'Transfer call outcome uncertain lotId=%s truckAssetId=%s tankAssetId=%s: %s' %
			(lotId, truckAssetId, tankAssetId, str(exc))
		)
		operationEventId = None
		message = str(exc)

	truckActivity = _getLotActivityAtAsset(lotId, truckAssetId)
	tankActivity = _getLotActivityAtAsset(lotId, tankAssetId)
	if tankActivity and not truckActivity:
		return makeResult('SUCCESS', 'Transfer completed.', {
			'lotId': int(lotId), 'lotName': activity.get('lotName'),
			'quantityKg': transferQty, 'truckAssetId': int(truckAssetId),
			'truckName': truck.get('assetName'), 'tankAssetId': int(tankAssetId),
			'tankName': tank.get('assetName'), 'transferOperationEventId': operationEventId
		})
	if truckActivity and not tankActivity:
		return makeResult('TRANSFER_PENDING', 'The lot remains at the truck. Retry the transfer or use Pending Transfers.', {
			'lotId': int(lotId), 'lotName': activity.get('lotName'),
			'quantityKg': transferQty, 'truckAssetId': int(truckAssetId),
			'truckName': truck.get('assetName'), 'tankAssetId': int(tankAssetId),
			'tankName': tank.get('assetName'), 'transferMessage': message
		})

	getLogger().error(
		'Transfer requires reconciliation lotId=%s truckAssetId=%s tankAssetId=%s operationEventId=%s message=%s' %
		(lotId, truckAssetId, tankAssetId, operationEventId, message)
	)
	return makeResult('RECONCILIATION_REQUIRED', 'Transfer outcome could not be confirmed. Check lot activity before retrying.', {
		'lotId': int(lotId), 'lotName': activity.get('lotName'),
		'quantityKg': transferQty, 'truckAssetId': int(truckAssetId),
		'tankAssetId': int(tankAssetId), 'transferOperationEventId': operationEventId
	})


def receiveOrder(workOrderId, actualQtyKg, truckAssetId, tankAssetId, authUser):
	"""Create one Receive output, then transfer that lot to its selected tank.

	Args:
		workOrderId (int): Stable Kanoa production order identifier.
		actualQtyKg (float): Positive receipt quantity in kg.
		truckAssetId (int): Selected Receiving Storage Location.
		tankAssetId (int): Selected Bulk Storage Storage Location.
		authUser (dict): Authenticated Perspective session user.
	Returns:
		dict: Shared receipt, transfer, failure, or reconciliation outcome.
	Updated:
		2026-11-13: Initial implementation.
	"""
	from decimal import Decimal, InvalidOperation
	try:
		workOrderId = int(workOrderId)
		truckAssetId = int(truckAssetId)
		tankAssetId = int(tankAssetId)
		qtyDecimal = Decimal(str(actualQtyKg))
	except (TypeError, ValueError, InvalidOperation):
		return makeResult('VALIDATION_ERROR', 'Enter a positive receipt quantity and select an order, truck, and tank.')
	if not qtyDecimal.is_finite() or qtyDecimal <= 0:
		return makeResult('VALIDATION_ERROR', 'Actual quantity must be greater than zero kg.')
	qty = float(qtyDecimal)

	try:
		userId = getAuthenticatedUserId(authUser)
	except Exception as exc:
		return makeResult('AUTHENTICATION_ERROR', str(exc))

	lock = _acquireOrderLock(workOrderId)
	lockHeld = True
	try:
		getLogger().info('Receive start workOrderId=%s truckAssetId=%s tankAssetId=%s qtyKg=%s userId=%s' %
			(workOrderId, truckAssetId, tankAssetId, qty, userId))
		order = _getOrder(workOrderId)
		if not order or order.get('workOrderStatusName') not in ('Scheduled', 'In Progress'):
			return makeResult('NOT_ELIGIBLE', 'This order is no longer eligible for receiving. Refresh the schedule.')
		if (order.get('itemUnitName') or '').strip().lower() != 'kg':
			return makeResult('UNIT_ERROR', 'This order is not in kg. Receiving is blocked until its unit conversion is verified.')
		try:
			targetQtyDecimal = Decimal(str(order.get('reqdQty')))
		except (TypeError, ValueError, InvalidOperation):
			return makeResult('DATA_ERROR', 'The order target quantity is unavailable. Ask a supervisor to correct the order.')
		if not targetQtyDecimal.is_finite() or targetQtyDecimal <= 0:
			return makeResult('DATA_ERROR', 'The order target quantity must be greater than zero.')

		receivedResult = getReceivedQtyForOrder(workOrderId)
		if receivedResult['status'] != 'SUCCESS':
			return receivedResult
		receivedQtyDecimal = Decimal(receivedResult['data']['receivedQtyKgExact'])
		remainingDecimal = targetQtyDecimal - receivedQtyDecimal
		if qtyDecimal > remainingDecimal:
			remaining = float(max(Decimal('0'), remainingDecimal))
			return makeResult('VALIDATION_ERROR', 'Quantity exceeds the remaining order target of %s kg.' % remaining, {
				'receivedQtyKg': float(receivedQtyDecimal), 'remainingQtyKg': remaining,
				'targetQtyKg': float(targetQtyDecimal)
			})

		truck = _getEligibleAsset(truckAssetId, 'Training Plant\\Receiving')
		tank = _getEligibleAsset(tankAssetId, 'Training Plant\\Bulk Storage')
		if not truck or not tank:
			return makeResult('VALIDATION_ERROR', 'The selected truck or tank is no longer eligible. Refresh the asset lists.')
		if order.get('itemId') is None:
			return makeResult('DATA_ERROR', 'The order has no material configured. Ask a supervisor to correct it.')

		configurationResult = getReceivingConfiguration(_receivingSerialName)
		if configurationResult['status'] != 'SUCCESS':
			return configurationResult
		configuration = configurationResult['data']

		lotName, serialMessage = system.kanoa.serial.getNextSerialNumber(configuration['serialId'], userId)
		if serialMessage or not lotName:
			getLogger().error('Receive serial allocation failed workOrderId=%s userId=%s message=%s' %
				(workOrderId, userId, serialMessage))
			return makeResult('RECEIPT_FAILED', 'A lot number could not be allocated. No receipt was recorded.')

		outputEvent = {
			'lotEventId': None,
			'lotId': None,
			'lotName': lotName,
			'itemId': order.get('itemId'),
			'itemUnitId': configuration['kgUnitId'],
			'lotEventQty': qty,
			'workOrderId': workOrderId,
			'assetId': truckAssetId,
			'itemSourceId': configuration['outputSourceId'],
			'lotStateId': configuration['initialLotStateId'],
			'lotStateReasonId': None,
			'shiftId': None,
			'tStamp': system.date.now(),
			'comment': None,
			'lotOperationEventId': None,
			'assetTransportId': None
		}
		operationInfo = {
			'lotOperationEventId': None,
			'lotOperationId': configuration['receiveOperationId'],
			'assetId': truckAssetId,
			'tStamp': system.date.now(),
			'enabled': True
		}

		getLogger().info('Receive write start workOrderId=%s lotName=%s truckAssetId=%s qtyKg=%s userId=%s' %
			(workOrderId, lotName, truckAssetId, qty, userId))
		try:
			receiveOperationEventId, receiveMessage = system.kanoa.lot.executeLotOperation(
				operationInfo, [], [outputEvent], userId
			)
		except Exception as exc:
			getLogger().error('Receive outcome uncertain workOrderId=%s lotName=%s: %s' %
				(workOrderId, lotName, str(exc)))
			reconcileResult = checkReceiptAttempt(workOrderId, lotName)
			if reconcileResult['status'] != 'SUCCESS':
				reconcileResult['data'].update({
					'workOrderId': workOrderId, 'lotName': lotName, 'quantityKg': qty,
					'truckAssetId': truckAssetId, 'truckName': truck.get('assetName')
				})
				return reconcileResult
			receiveOperationEventId = reconcileResult['data'].get('receiveOperationEventId')
			receiveMessage = None
		if receiveMessage or receiveOperationEventId is None:
			getLogger().error('Receive returned failure workOrderId=%s lotName=%s operationEventId=%s message=%s' %
				(workOrderId, lotName, receiveOperationEventId, receiveMessage))
			reconcileResult = checkReceiptAttempt(workOrderId, lotName)
			if reconcileResult['status'] != 'SUCCESS':
				reconcileResult['data'].update({
					'workOrderId': workOrderId, 'lotName': lotName, 'quantityKg': qty,
					'truckAssetId': truckAssetId, 'truckName': truck.get('assetName'),
					'receiveOperationEventId': receiveOperationEventId
				})
				return reconcileResult
			receiveOperationEventId = reconcileResult['data'].get('receiveOperationEventId')

		lotId = _findLotId(lotName)
		if lotId is None:
			getLogger().error('Receive committed but lot lookup failed workOrderId=%s lotName=%s operationEventId=%s' %
				(workOrderId, lotName, receiveOperationEventId))
			return makeResult('RECONCILIATION_REQUIRED', 'Receipt was recorded but the lot could not be reloaded. Ask a supervisor to reconcile it.', {
				'workOrderId': workOrderId, 'lotName': lotName, 'quantityKg': qty,
				'receiveOperationEventId': receiveOperationEventId
			})

		_releaseResourceLock(lock)
		lockHeld = False
		transferResult = _performTransfer(lotId, truckAssetId, tankAssetId, qty, userId, configuration)
		transferResult['data'].update({
			'workOrderId': workOrderId,
			'orderNumber': order.get('workOrderName'),
			'receiveOperationEventId': receiveOperationEventId,
			'quantityKg': qty,
			'lotId': lotId,
			'lotName': lotName
		})
		getLogger().info('Receive outcome workOrderId=%s lotId=%s receiveOperationEventId=%s status=%s' %
			(workOrderId, lotId, receiveOperationEventId, transferResult['status']))
		return transferResult
	finally:
		if lockHeld:
			_releaseResourceLock(lock)


def getPendingTransfers():
	"""List positive lot quantities currently located at enabled Receiving trucks.

	Args:
		None
	Returns:
		dict: Shared result containing current truck inventory rows.
	Updated:
		2026-11-13: Initial implementation.
	"""
	assetsResult = getReceivingAssets()
	if assetsResult['status'] != 'SUCCESS':
		return assetsResult

	try:
		pending = []
		seen = set()
		for truck in assetsResult['data']['trucks']:
			activityRows = _datasetRows(system.kanoa.lot.getLotActivity({
				'assetId': truck['assetId'], 'hasQty': True
			}))
			for activity in activityRows:
				try:
					qty = float(activity.get('lotEventQty'))
				except (TypeError, ValueError):
					continue
				if qty <= 0:
					continue
				key = (activity.get('lotId'), truck.get('assetId'))
				if key in seen:
					continue
				seen.add(key)
				order = _getOrder(activity.get('workOrderId')) if activity.get('workOrderId') is not None else None
				pending.append({
					'lotId': activity.get('lotId'),
					'lotName': activity.get('lotName'),
					'itemId': activity.get('itemId'),
					'material': activity.get('itemName'),
					'workOrderId': activity.get('workOrderId'),
					'orderNumber': order.get('workOrderName') if order else None,
					'quantity': qty,
					'unitName': activity.get('itemUnitName'),
					'truckAssetId': truck.get('assetId'),
					'truckName': truck.get('assetName'),
					'truckPath': truck.get('assetPath')
				})
		pending.sort(key=lambda row: (row.get('orderNumber') or '', row.get('lotName') or '', row.get('truckName') or ''))
		return makeResult('SUCCESS', 'Pending truck inventory loaded.', {'pendingTransfers': pending})
	except Exception as exc:
		getLogger().error('getPendingTransfers() failed: %s' % str(exc))
		return makeResult('ERROR', 'Could not load current truck inventory. Refresh the list or contact a supervisor.')


def retryTransfer(lotId, tankAssetId, authUser, truckAssetId=None):
	"""Transfer an existing lot from a Receiving truck without repeating receipt.

	Args:
		lotId (int): Existing Kanoa lot ID.
		tankAssetId (int): Selected Bulk Storage Storage Location.
		authUser (dict): Authenticated Perspective session user.
		truckAssetId (int): Optional selected current Receiving truck.
	Returns:
		dict: Shared transfer or reconciliation outcome.
	Updated:
		2026-11-13: Initial implementation.
	"""
	try:
		lotId = int(lotId)
		tankAssetId = int(tankAssetId)
		if truckAssetId is not None:
			truckAssetId = int(truckAssetId)
		userId = getAuthenticatedUserId(authUser)
	except (TypeError, ValueError) as exc:
		return makeResult('VALIDATION_ERROR', str(exc) or 'Select a lot, truck, and destination tank.')
	except Exception as exc:
		return makeResult('AUTHENTICATION_ERROR', str(exc))

	configurationResult = _getTransferConfiguration()
	if configurationResult['status'] != 'SUCCESS':
		return configurationResult

	try:
		rows = _datasetRows(system.kanoa.lot.getLotActivity({'lotId': lotId, 'hasQty': True}))
	except Exception as exc:
		getLogger().error('retryTransfer() activity lookup failed lotId=%s: %s' % (lotId, str(exc)))
		return makeResult('ERROR', 'Could not confirm the lot location. Refresh pending transfers before retrying.')

	eligible = []
	for row in rows:
		assetId = row.get('assetId')
		try:
			qty = float(row.get('lotEventQty'))
		except (TypeError, ValueError):
			continue
		if qty <= 0:
			continue
		if truckAssetId is not None and int(assetId) != truckAssetId:
			continue
		if _getEligibleAsset(assetId, 'Training Plant\\Receiving'):
			eligible.append(row)
	if len(eligible) != 1:
		return makeResult('NOT_ELIGIBLE', 'This lot is no longer at exactly one eligible Receiving truck. Refresh pending transfers.')

	activity = eligible[0]
	truckAssetId = int(activity.get('assetId'))
	tank = _getEligibleAsset(tankAssetId, 'Training Plant\\Bulk Storage')
	if not tank:
		return makeResult('VALIDATION_ERROR', 'The selected tank is no longer eligible. Refresh the asset list.')

	configuration = configurationResult['data']
	result = _performTransfer(lotId, truckAssetId, tankAssetId, activity.get('lotEventQty'), userId, configuration)
	getLogger().info('retryTransfer outcome lotId=%s truckAssetId=%s tankAssetId=%s status=%s' %
		(lotId, truckAssetId, tankAssetId, result['status']))
	return result
