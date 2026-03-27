ProofWrapperApi:
    -> __init__()

    -> init(lifecycle_id) -> Union[ValueMessage, NotifyMessage]:
        test if return is true Union[ValueMessage, NotifyMessage]

    -> step(lifecycle_id) -> -> Union[ValueMessage, NotifyMessage]
        test communication_point
        test if return is true Union[ValueMessage, NotifyMessage]

    -> get_data() -> Dict
        test if return is true Dict type
        test if return has correct keys / values

    -> send_value(lifecycle_id) -> ValueMessage
        test if functions return true ValueMessage object
        test if value message is correct:
            communication_step_size
            communication_point
            lifeCycleId
            type
            data -> get_data() ???
            time not possible ?
        test value.json()

    -> send_notify() -> NotifyMessage
        test if functions return true NotifyMessage object
        test if notify message is correct:
            communication_step_size
            communication_point
            status
            lifeCycleId
            type
            time not possible ?
        test notify.json()

    -> finalize(lifecycle_id) -> Union[ValueMessage, NotifyMessage]:
        test if return is true Union[ValueMessage, NotifyMessage]

-> value_function(message: ValueMessage, model) -> None
    test if values are set correctly

-> tact_function(message: TactMessage, model) -> None
    testen ob Thread gestartet und beendet wird ?
    testen ob model variables gesetzt werden ?
    testen ob step_function richtig ausgewählt wird ?

-> main(model) -> None
